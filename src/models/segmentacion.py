"""Comparación exploratoria de algoritmos de clusterización mixta."""
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERICAS = [
    "edad",
    "personas_hogar",
    "personas_a_cargo",
    "ingreso_neto_mensual_cop",
    "gastos_esenciales_mensuales_cop",
    "cuotas_deudas_vigentes_cop",
    "ahorro_disponible_cop",
    "meses_historial_crediticio",
    "moras_ultimos_12_meses",
    "monto_solicitado_cop",
]
CATEGORICAS = [
    "tipo_hogar",
    "nivel_estudio",
    "situacion_laboral",
    "tipo_ingreso",
    "tiene_vivienda_propia",
    "tiene_vehiculo",
    "tipo_plan_celular",
    "experiencia_crediticia",
]
CATEGORICAS_BASE_FINAL = [
    "tipo_hogar",
    "situacion_laboral",
    "tipo_ingreso",
    "tiene_vivienda_propia",
    "tiene_vehiculo",
    "experiencia_crediticia",
]
NUMERICAS_BASE_FINAL = [
    "edad", "personas_hogar", "personas_a_cargo", "ingreso_per_capita_cop",
    "ratio_gastos_ingreso", "ratio_deuda_ingreso", "cobertura_ahorro_meses",
    "meses_historial_crediticio", "moras_ultimos_12_meses", "monto_solicitado_cop",
]
MONTOS = [
    "ingreso_neto_mensual_cop",
    "gastos_esenciales_mensuales_cop",
    "cuotas_deudas_vigentes_cop",
    "ahorro_disponible_cop",
    "monto_solicitado_cop",
    "ingreso_per_capita_cop",
]


def _seleccionar(
    df: pd.DataFrame,
    columnas_categoricas=None,
    columnas_numericas=None,
    imputar_faltantes=True,
):
    categoricas_configuradas = CATEGORICAS if columnas_categoricas is None else list(columnas_categoricas)
    numericas_configuradas = NUMERICAS if columnas_numericas is None else list(columnas_numericas)
    faltan = sorted(set(numericas_configuradas + categoricas_configuradas) - set(df.columns))
    if faltan:
        raise ValueError(f"Faltan campos requeridos para clusterizar: {faltan}")
    numericas = df[numericas_configuradas].astype(float).copy()
    for columna in MONTOS:
        if columna in numericas.columns:
            numericas[columna] = np.log1p(numericas[columna].clip(lower=0))
    numericas = numericas.replace([np.inf, -np.inf], np.nan)
    if imputar_faltantes:
        numericas = numericas.fillna(numericas.median())
    numericas = numericas.to_numpy(dtype=np.float64)
    categoricas = df[categoricas_configuradas].fillna("sin_dato").astype(str).to_numpy(dtype=object)
    return numericas, categoricas


def _distancia_kproto(numericas, categoricas, centros_num, centros_cat, gamma):
    dist_num = ((numericas[:, None, :] - centros_num[None, :, :]) ** 2).sum(axis=2)
    dist_cat = (categoricas[:, None, :] != centros_cat[None, :, :]).sum(axis=2)
    return dist_num + gamma * dist_cat


@dataclass
class KPrototypesPerfil:
    scaler: StandardScaler
    centros_num: np.ndarray
    centros_cat: np.ndarray
    gamma: float = 1.0

    def predict(self, numericas, categoricas):
        x_num = self.scaler.transform(numericas)
        return _distancia_kproto(x_num, categoricas, self.centros_num, self.centros_cat, self.gamma).argmin(axis=1)


@dataclass
class KPrototypesPredictor:
    """Predictor serializable para la API, con el esquema mixto de la base final."""

    scaler: StandardScaler
    centros_num: np.ndarray
    centros_cat: np.ndarray
    imputaciones_numericas: dict[str, float]
    columnas_numericas: tuple[str, ...]
    columnas_categoricas: tuple[str, ...]
    gamma: float
    k: int
    seed: int
    max_iter: int
    cluster_profiles: list[dict]
    cluster_routes: dict[str, str]
    dataset_size: int

    def predict(self, df: pd.DataFrame):
        numericas, categoricas = _seleccionar(
            df, self.columnas_categoricas, self.columnas_numericas,
            imputar_faltantes=False,
        )
        numericas = numericas.copy()
        for j, columna in enumerate(self.columnas_numericas):
            numericas[:, j] = np.where(
                np.isfinite(numericas[:, j]),
                numericas[:, j],
                self.imputaciones_numericas[columna],
            )
        normalizadas = self.scaler.transform(numericas)
        distancias = _distancia_kproto(
            normalizadas, categoricas, self.centros_num, self.centros_cat, self.gamma
        )
        return distancias.argmin(axis=1), distancias.min(axis=1)


def _fit_kprototypes(numericas, categoricas, k, seed, gamma=1.0, max_iter=30):
    scaler = StandardScaler()
    x_num = scaler.fit_transform(numericas)
    rng = np.random.default_rng(seed)
    iniciales = rng.choice(len(x_num), size=k, replace=False)
    centros_num = x_num[iniciales].copy()
    centros_cat = categoricas[iniciales].copy()
    labels_prev = None

    for _ in range(max_iter):
        distancias = _distancia_kproto(x_num, categoricas, centros_num, centros_cat, gamma)
        labels = distancias.argmin(axis=1)
        cercania = distancias.min(axis=1)
        for grupo in range(k):
            miembros = labels == grupo
            if not miembros.any():
                reemplazo = int(cercania.argmax())
                centros_num[grupo] = x_num[reemplazo]
                centros_cat[grupo] = categoricas[reemplazo]
                cercania[reemplazo] = -1
                continue
            centros_num[grupo] = x_num[miembros].mean(axis=0)
            for j in range(categoricas.shape[1]):
                valores, conteos = np.unique(categoricas[miembros, j], return_counts=True)
                centros_cat[grupo, j] = valores[conteos.argmax()]
        if labels_prev is not None and np.array_equal(labels, labels_prev):
            break
        labels_prev = labels

    modelo = KPrototypesPerfil(scaler, centros_num, centros_cat, gamma)
    return modelo, modelo.predict(numericas, categoricas)


@dataclass
class KMeansMixto:
    scaler: StandardScaler
    encoder: OneHotEncoder
    modelo: KMeans

    def transformar(self, numericas, categoricas):
        z_num = self.scaler.transform(numericas)
        z_cat = self.encoder.transform(categoricas) / np.sqrt(2.0)
        return hstack([csr_matrix(z_num), z_cat], format="csr", dtype=np.float32)

    def predict(self, numericas, categoricas):
        return self.modelo.predict(self.transformar(numericas, categoricas))


def _fit_kmeans_mixto(numericas, categoricas, k, seed):
    scaler = StandardScaler()
    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=True, dtype=np.float32)
    z_num = scaler.fit_transform(numericas)
    z_cat = encoder.fit_transform(categoricas) / np.sqrt(2.0)
    x = hstack([csr_matrix(z_num), z_cat], format="csr", dtype=np.float32)
    modelo = KMeans(n_clusters=k, n_init=10, random_state=seed)
    labels = modelo.fit_predict(x)
    return KMeansMixto(scaler, encoder, modelo), labels


def _preparar_gower(numericas, train_indices):
    """Calcula rangos de entrenamiento; los montos ya están en log1p."""
    x = numericas.copy()
    minimo = np.nanmin(x[train_indices], axis=0)
    maximo = np.nanmax(x[train_indices], axis=0)
    rangos = np.where(maximo > minimo, maximo - minimo, 1.0)
    return x, minimo, rangos


def _gower(a_num, a_cat, b_num, b_cat, minimo, rangos, feature_weights=None):
    n_features = a_num.shape[1] + a_cat.shape[1]
    pesos = (
        np.ones(n_features, dtype=np.float32)
        if feature_weights is None
        else np.asarray(feature_weights, dtype=np.float32)
    )
    if pesos.shape != (n_features,) or np.any(~np.isfinite(pesos)) or np.any(pesos <= 0):
        raise ValueError("feature_weights debe tener un peso positivo por variable.")
    distancia = np.zeros((len(a_num), len(b_num)), dtype=np.float32)
    comparables = np.zeros_like(distancia)
    for j in range(a_num.shape[1]):
        diferencia = np.abs(a_num[:, None, j] - b_num[None, :, j]) / rangos[j]
        valido = np.isfinite(diferencia)
        distancia += np.where(valido, np.minimum(diferencia, 1.0) * pesos[j], 0.0).astype(np.float32)
        comparables += valido * pesos[j]
    for j in range(a_cat.shape[1]):
        peso = pesos[a_num.shape[1] + j]
        distancia += (a_cat[:, None, j] != b_cat[None, :, j]).astype(np.float32) * peso
        comparables += peso
    return np.divide(distancia, comparables, out=np.zeros_like(distancia), where=comparables > 0)


def _pam_muestreado(
    distancias,
    k,
    seed,
    swap_candidates=None,
    max_iter=50,
    n_starts=20,
):
    """PAM mult inicio; prueba todos los swaps salvo que se limite candidatos."""
    if n_starts < 1 or max_iter < 1:
        raise ValueError("n_starts y max_iter deben ser al menos 1.")
    rng = np.random.default_rng(seed)
    n = len(distancias)
    mejores_medoids = None
    mejor_costo = np.inf
    mejor_iteraciones = 0

    for _ in range(n_starts):
        medoids = rng.choice(n, size=k, replace=False)
        costo = np.min(distancias[:, medoids], axis=1).sum()
        iteraciones = 0

        for iteraciones in range(1, max_iter + 1):
            no_medoids = np.setdiff1d(np.arange(n), medoids, assume_unique=False)
            if swap_candidates is not None and len(no_medoids) > swap_candidates:
                candidatos = rng.choice(no_medoids, size=swap_candidates, replace=False)
            else:
                candidatos = no_medoids
            mejor_costo_swap = costo
            mejor_swap = None
            for posicion in range(k):
                otros = np.delete(medoids, posicion)
                base = np.min(distancias[:, otros], axis=1)
                costos = np.minimum(base[:, None], distancias[:, candidatos]).sum(axis=0)
                idx = int(costos.argmin())
                if costos[idx] < mejor_costo_swap - 1e-8:
                    mejor_costo_swap = float(costos[idx])
                    mejor_swap = (posicion, int(candidatos[idx]))
            if mejor_swap is None:
                break
            medoids[mejor_swap[0]] = mejor_swap[1]
            costo = mejor_costo_swap

        if costo < mejor_costo:
            mejores_medoids = medoids.copy()
            mejor_costo = float(costo)
            mejor_iteraciones = iteraciones

    labels = np.argmin(distancias[:, mejores_medoids], axis=1)
    return mejores_medoids, labels, mejor_costo, mejor_iteraciones


@dataclass
class GowerKMedoidsPredictor:
    """Modelo mínimo para asignar perfiles nuevos a medoides ya ajustados."""

    medoids_num: np.ndarray
    medoids_cat: np.ndarray
    minimo: np.ndarray
    rangos: np.ndarray
    k: int
    seed: int
    train_sample_size: int
    n_starts: int
    max_iter: int
    cluster_profiles: list[dict]
    dataset_size: int = 0
    columnas_numericas: tuple[str, ...] = tuple(NUMERICAS)
    columnas_categoricas: tuple[str, ...] = tuple(CATEGORICAS)
    winsor99_limits: dict[str, float] | None = None

    def predict(self, df: pd.DataFrame):
        numericas, categoricas = _seleccionar(
            df, self.columnas_categoricas, self.columnas_numericas,
            imputar_faltantes=False,
        )
        numericas = numericas.copy()
        if self.winsor99_limits:
            for j, columna in enumerate(self.columnas_numericas):
                if columna in self.winsor99_limits:
                    numericas[:, j] = np.log1p(np.minimum(
                        np.clip(numericas[:, j], 0, None), self.winsor99_limits[columna]
                    ))
        distancias = _gower(
            numericas, categoricas,
            self.medoids_num, self.medoids_cat,
            self.minimo, self.rangos,
        )
        labels = distancias.argmin(axis=1)
        distancias_minimas = distancias.min(axis=1)
        return labels, distancias_minimas


def _resumir_clusters(df: pd.DataFrame, labels) -> list[dict]:
    datos = df.copy()
    datos["cluster"] = np.asarray(labels)
    numericas = [
        "edad", "personas_a_cargo", "ingreso_neto_mensual_cop",
        "gastos_esenciales_mensuales_cop", "cuotas_deudas_vigentes_cop",
        "flujo_mensual_disponible_cop", "meses_historial_crediticio",
    ]
    categoricas = ["situacion_laboral", "tipo_ingreso", "experiencia_crediticia"]
    perfiles = []
    for cluster, grupo in datos.groupby("cluster", sort=True):
        mediana = grupo[numericas].median().round(0).astype(int).to_dict()
        moda = {
            campo: str(grupo[campo].mode().iloc[0])
            for campo in categoricas
        }
        nivel = (grupo["nivel_educacion_financiera"]
                 .value_counts(normalize=True).mul(100).round(1).to_dict())
        perfiles.append({
            "cluster_id": int(cluster),
            "perfiles": int(len(grupo)),
            "porcentaje": round(len(grupo) / len(datos) * 100, 1),
            "medianas": mediana,
            "categorias_mas_frecuentes": moda,
            "educacion_financiera_proxy_pct": nivel,
        })
    return perfiles


def _mapear_rutas_por_perfil(perfiles: list[dict]) -> dict[str, str]:
    """Asocia IDs arbitrarios a rutas usando historial y flujo medianos."""
    por_cluster = {p["cluster_id"]: p["medianas"] for p in perfiles}
    educacion = min(por_cluster, key=lambda c: por_cluster[c]["meses_historial_crediticio"])
    viabilidad = max(
        (c for c in por_cluster if c != educacion),
        key=lambda c: (
            por_cluster[c]["meses_historial_crediticio"],
            por_cluster[c]["flujo_mensual_disponible_cop"],
        ),
    )
    cuidar = next(c for c in por_cluster if c not in {educacion, viabilidad})
    return {
        str(educacion): "educacion_financiera",
        str(viabilidad): "viabilidad_formal",
        str(cuidar): "cuidar_historial",
    }


def ajustar_kprototypes_api(
    df: pd.DataFrame,
    k=3,
    seed=42,
    gamma=1.0,
    max_iter=30,
    columnas_categoricas=None,
    columnas_numericas=None,
) -> KPrototypesPredictor:
    """Ajusta el K-Prototypes académico y prepara el predictor de la API."""
    columnas_categoricas = tuple(columnas_categoricas or CATEGORICAS)
    columnas_numericas = tuple(columnas_numericas or NUMERICAS)
    numericas, categoricas = _seleccionar(
        df, columnas_categoricas, columnas_numericas, imputar_faltantes=False
    )
    numericas = numericas.copy()
    imputaciones = {
        columna: float(np.nanmedian(numericas[:, j]))
        for j, columna in enumerate(columnas_numericas)
    }
    for j, columna in enumerate(columnas_numericas):
        numericas[:, j] = np.where(
            np.isfinite(numericas[:, j]), numericas[:, j], imputaciones[columna]
        )
    modelo, labels = _fit_kprototypes(
        numericas, categoricas, k, seed, gamma=gamma, max_iter=max_iter
    )
    perfiles = _resumir_clusters(df, labels)
    return KPrototypesPredictor(
        scaler=modelo.scaler,
        centros_num=modelo.centros_num,
        centros_cat=modelo.centros_cat,
        imputaciones_numericas=imputaciones,
        columnas_numericas=columnas_numericas,
        columnas_categoricas=columnas_categoricas,
        gamma=gamma,
        k=k,
        seed=seed,
        max_iter=max_iter,
        cluster_profiles=perfiles,
        cluster_routes=_mapear_rutas_por_perfil(perfiles),
        dataset_size=len(df),
    )


def ajustar_gower_kmedoids(
    df: pd.DataFrame,
    k=3,
    seed=42,
    train_sample_size=1800,
    n_starts=20,
    max_iter=50,
    columnas_categoricas=None,
    columnas_numericas=None,
    transformacion_relativas="none",
) -> GowerKMedoidsPredictor:
    """Ajusta medoids Gower en una muestra y crea predictor serializable."""
    columnas_categoricas = tuple(columnas_categoricas or CATEGORICAS)
    columnas_numericas = tuple(columnas_numericas or NUMERICAS)
    numericas, categoricas = _seleccionar(
        df, columnas_categoricas, columnas_numericas, imputar_faltantes=False
    )
    numericas = numericas.copy()
    if len(df) < max(train_sample_size, k):
        raise ValueError("No hay suficientes perfiles para el tamaño de ajuste elegido.")
    rng = np.random.default_rng(seed)
    sample_indices = rng.choice(len(df), size=train_sample_size, replace=False)
    winsor99_limits = {}
    if transformacion_relativas not in {"none", "log1p", "winsor99_log1p"}:
        raise ValueError("transformacion_relativas debe ser none, log1p o winsor99_log1p.")
    if transformacion_relativas != "none":
        relativas = {"ratio_deuda_ingreso", "ratio_gastos_ingreso", "cobertura_ahorro_meses"}
        for j, columna in enumerate(columnas_numericas):
            if columna not in relativas:
                continue
            valores = numericas[:, j]
            if transformacion_relativas == "winsor99_log1p":
                limite = float(np.nanquantile(valores[sample_indices], 0.99))
                winsor99_limits[columna] = limite
                valores = np.minimum(valores, limite)
            numericas[:, j] = np.log1p(np.clip(valores, 0, None))
    _, minimo, rangos = _preparar_gower(numericas, sample_indices)
    train_num = numericas[sample_indices]
    train_cat = categoricas[sample_indices]
    d_train = _gower(train_num, train_cat, train_num, train_cat, minimo, rangos)
    np.fill_diagonal(d_train, 0.0)
    medoids_locales, _, _, _ = _pam_muestreado(
        d_train, k, seed + 100 + k,
        max_iter=max_iter, n_starts=n_starts,
    )
    medoids_globales = sample_indices[medoids_locales]
    predictor = GowerKMedoidsPredictor(
        medoids_num=numericas[medoids_globales].copy(),
        medoids_cat=categoricas[medoids_globales].copy(),
        minimo=minimo,
        rangos=rangos,
        k=k,
        seed=seed,
        train_sample_size=train_sample_size,
        n_starts=n_starts,
        max_iter=max_iter,
        cluster_profiles=[],
        columnas_numericas=columnas_numericas,
        columnas_categoricas=columnas_categoricas,
        winsor99_limits=winsor99_limits or None,
    )
    labels, _ = predictor.predict(df)
    predictor.cluster_profiles = _resumir_clusters(df, labels)
    predictor.medoid_profile_ids = (
        df.iloc[medoids_globales]["id_persona"].astype(str).tolist()
        if "id_persona" in df.columns else []
    )
    return predictor


def comparar_clusterizaciones(
    df: pd.DataFrame,
    k_values=(3, 4, 5, 6),
    seed=42,
    gower_train_size=1800,
    evaluation_size=800,
    pam_starts=20,
    pam_max_iter=50,
    columnas_categoricas=None,
    columnas_numericas=None,
    transformacion_relativas="none",
    estrategia_faltantes="mediana",
):
    """Ajusta tres métodos y compara silhouette Gower en una evaluación común.

    K-Prototypes y K-Means mixto se ajustan con los perfiles fuera de la muestra
    común de evaluación. Gower + PAM usa una muestra acotada por su coste
    cuadrático. Todos se evalúan sobre los mismos perfiles con distancia Gower.
    """
    numericas, categoricas = _seleccionar(df, columnas_categoricas, columnas_numericas)
    if estrategia_faltantes not in {"mediana", "pairwise"}:
        raise ValueError("estrategia_faltantes debe ser mediana o pairwise.")
    numericas_gower = numericas.copy()
    if estrategia_faltantes == "pairwise":
        numericas_gower, _ = _seleccionar(
            df, columnas_categoricas, columnas_numericas, imputar_faltantes=False
        )
    n = len(df)
    if n < max(gower_train_size + evaluation_size, 100):
        raise ValueError("La base es demasiado pequeña para los tamaños de muestra elegidos.")
    rng = np.random.default_rng(seed)
    permutacion = rng.permutation(n)
    n_eval = min(evaluation_size, max(50, int(n * 0.20)))
    eval_idx = permutacion[:n_eval]
    train_idx = permutacion[n_eval:]
    if len(train_idx) < max(k_values):
        raise ValueError("No hay suficientes filas para ajustar los k indicados.")

    if transformacion_relativas not in {"none", "log1p", "winsor99_log1p"}:
        raise ValueError("transformacion_relativas debe ser none, log1p o winsor99_log1p.")
    columnas_relativas = {
        "ratio_deuda_ingreso",
        "ratio_gastos_ingreso",
        "cobertura_ahorro_meses",
    }
    for j, columna in enumerate(columnas_numericas or NUMERICAS):
        if columna not in columnas_relativas or transformacion_relativas == "none":
            continue
        valores = numericas[:, j]
        valores_gower = numericas_gower[:, j]
        if transformacion_relativas == "winsor99_log1p":
            limite = np.nanquantile(valores_gower[train_idx], 0.99)
            valores = np.minimum(valores, limite)
            valores_gower = np.minimum(valores_gower, limite)
        numericas[:, j] = np.log1p(np.clip(valores, 0, None))
        numericas_gower[:, j] = np.log1p(np.clip(valores_gower, 0, None))

    # Transformación común de valores monetarios para la distancia Gower.
    gower_num, minimo, rangos = _preparar_gower(numericas_gower, train_idx)
    gower_eval = _gower(
        gower_num[eval_idx], categoricas[eval_idx],
        gower_num[eval_idx], categoricas[eval_idx], minimo, rangos,
    )
    np.fill_diagonal(gower_eval, 0.0)

    gower_train_idx = rng.choice(train_idx, size=min(gower_train_size, len(train_idx)), replace=False)
    d_train_gower = _gower(
        gower_num[gower_train_idx], categoricas[gower_train_idx],
        gower_num[gower_train_idx], categoricas[gower_train_idx], minimo, rangos,
    )
    np.fill_diagonal(d_train_gower, 0.0)
    resultados = []
    modelos = {}
    labels_completos = {}

    for k in k_values:
        # 1) K-Prototypes: prototipos numéricos y modas categóricas.
        inicio = perf_counter()
        modelo, _ = _fit_kprototypes(numericas[train_idx], categoricas[train_idx], k, seed + k)
        eval_labels = modelo.predict(numericas[eval_idx], categoricas[eval_idx])
        tiempo = perf_counter() - inicio
        score = silhouette_score(gower_eval, eval_labels, metric="precomputed")
        key = ("K-Prototypes", k)
        resultados.append(_fila_resultado(key[0], k, score, tiempo, eval_labels))
        modelos[key] = modelo
        labels_completos[key] = modelo.predict(numericas, categoricas)

        # 2) K-Means sobre variables numéricas escaladas y one-hot categóricas.
        inicio = perf_counter()
        modelo, _ = _fit_kmeans_mixto(numericas[train_idx], categoricas[train_idx], k, seed + k)
        eval_labels = modelo.predict(numericas[eval_idx], categoricas[eval_idx])
        tiempo = perf_counter() - inicio
        score = silhouette_score(gower_eval, eval_labels, metric="precomputed")
        key = ("One-Hot + K-Means", k)
        resultados.append(_fila_resultado(key[0], k, score, tiempo, eval_labels))
        modelos[key] = modelo
        labels_completos[key] = modelo.predict(numericas, categoricas)

        # 3) PAM/K-Medoids con distancia Gower en muestra de entrenamiento.
        inicio = perf_counter()
        medoids_locales, _, pam_cost, pam_iterations = _pam_muestreado(
            d_train_gower, k, seed + 100 + k,
            max_iter=pam_max_iter, n_starts=pam_starts,
        )
        medoid_indices = gower_train_idx[medoids_locales]
        d_eval_medoids = _gower(
            gower_num[eval_idx], categoricas[eval_idx],
            gower_num[medoid_indices], categoricas[medoid_indices], minimo, rangos,
        )
        eval_labels = d_eval_medoids.argmin(axis=1)
        tiempo = perf_counter() - inicio
        score = silhouette_score(gower_eval, eval_labels, metric="precomputed")
        key = ("Gower + K-Medoids (muestra)", k)
        fila = _fila_resultado(key[0], k, score, tiempo, eval_labels)
        fila.update({
            "pam_objetivo_entrenamiento": pam_cost,
            "pam_iteraciones_inicio_ganador": pam_iterations,
            "pam_inicios": pam_starts,
            "pam_max_iter": pam_max_iter,
        })
        resultados.append(fila)
        modelos[key] = (medoid_indices, gower_num, categoricas, minimo, rangos)
        d_all_medoids = _gower(
            gower_num, categoricas,
            gower_num[medoid_indices], categoricas[medoid_indices], minimo, rangos,
        )
        labels_completos[key] = d_all_medoids.argmin(axis=1)

    metricas = pd.DataFrame(resultados).sort_values(
        ["silhouette_gower", "menor_cluster_pct"], ascending=[False, False]
    ).reset_index(drop=True)
    elegido = (metricas.loc[0, "algoritmo"], int(metricas.loc[0, "k"]))
    etiquetas = pd.Series(labels_completos[elegido], index=df.index, name="cluster")
    return metricas, etiquetas, elegido, labels_completos


def analizar_estabilidad_gower_kmedoids(
    df: pd.DataFrame,
    k=3,
    seed=42,
    repeticiones=10,
    gower_train_size=1800,
    evaluation_size=800,
    pam_starts=20,
    pam_max_iter=50,
):
    """Compara asignaciones de Gower + K-Medoids bajo distintas muestras.

    Usa el mismo subconjunto de evaluación y cambia la muestra usada para
    elegir los medoides. ARI es invariante al nombre asignado a cada cluster.
    """
    if repeticiones < 2:
        raise ValueError("Se requieren al menos dos repeticiones para medir estabilidad.")
    numericas, categoricas = _seleccionar(df)
    n = len(df)
    if n < gower_train_size + evaluation_size:
        raise ValueError("La base es demasiado pequeña para los tamaños de muestra elegidos.")

    rng = np.random.default_rng(seed)
    permutacion = rng.permutation(n)
    n_eval = min(evaluation_size, max(50, int(n * 0.20)))
    eval_idx = permutacion[:n_eval]
    train_pool = permutacion[n_eval:]
    gower_num, minimo, rangos = _preparar_gower(numericas, train_pool)
    d_eval = _gower(
        gower_num[eval_idx], categoricas[eval_idx],
        gower_num[eval_idx], categoricas[eval_idx], minimo, rangos,
    )
    np.fill_diagonal(d_eval, 0.0)

    muestras = []
    distancias_muestras = []
    for repeticion in range(repeticiones):
        semilla = seed + repeticion
        rng_corrida = np.random.default_rng(semilla)
        muestra = rng_corrida.choice(
            train_pool, size=min(gower_train_size, len(train_pool)), replace=False
        )
        d_train = _gower(
            gower_num[muestra], categoricas[muestra],
            gower_num[muestra], categoricas[muestra], minimo, rangos,
        )
        np.fill_diagonal(d_train, 0.0)
        muestras.append(muestra)
        distancias_muestras.append(d_train)

    semilla_pam = seed + 100 + k

    def asignar(muestra, distancias, semilla_ajuste):
        medoids_locales, _, _, _ = _pam_muestreado(
            distancias, k, semilla_ajuste,
            max_iter=pam_max_iter, n_starts=pam_starts,
        )
        medoids = muestra[medoids_locales]
        d_eval_medoids = _gower(
            gower_num[eval_idx], categoricas[eval_idx],
            gower_num[medoids], categoricas[medoids], minimo, rangos,
        )
        return d_eval_medoids.argmin(axis=1)

    # Cambia la muestra y conserva la inicialización de PAM.
    labels_muestras = [
        asignar(muestra, d_train, semilla_pam)
        for muestra, d_train in zip(muestras, distancias_muestras)
    ]
    # Conserva la muestra y cambia la inicialización aleatoria de PAM.
    labels_inicializacion = [
        asignar(muestras[0], distancias_muestras[0], semilla_pam + repeticion)
        for repeticion in range(repeticiones)
    ]

    filas = []
    for repeticion, labels in enumerate(labels_muestras):
        conteos = np.bincount(labels, minlength=k)
        silhouette = (
            float(silhouette_score(d_eval, labels, metric="precomputed"))
            if 1 < len(np.unique(labels)) < len(labels)
            else np.nan
        )
        filas.append({
            "repeticion": repeticion + 1,
            "semilla_muestra": seed + repeticion,
            "silhouette_gower_evaluacion": silhouette,
            "ari_remuestreo_vs_referencia": float(
                adjusted_rand_score(labels_muestras[0], labels)
            ),
            "ari_inicializacion_vs_referencia": float(
                adjusted_rand_score(labels_inicializacion[0], labels_inicializacion[repeticion])
            ),
            "cluster_menor_pct": float(conteos.min() / len(labels) * 100),
            "cluster_mayor_pct": float(conteos.max() / len(labels) * 100),
        })
    return pd.DataFrame(filas)


def _fila_resultado(algoritmo, k, silhouette, segundos, labels):
    _, conteos = np.unique(labels, return_counts=True)
    porcentajes = conteos / len(labels) * 100
    return {
        "algoritmo": algoritmo,
        "k": k,
        "silhouette_gower": float(silhouette),
        "menor_cluster_pct": float(porcentajes.min()),
        "mayor_cluster_pct": float(porcentajes.max()),
        "tiempo_ajuste_segundos": float(segundos),
    }
