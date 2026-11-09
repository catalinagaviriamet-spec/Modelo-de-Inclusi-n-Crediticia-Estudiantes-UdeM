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
MONTOS = [
    "ingreso_neto_mensual_cop",
    "gastos_esenciales_mensuales_cop",
    "cuotas_deudas_vigentes_cop",
    "ahorro_disponible_cop",
    "monto_solicitado_cop",
]


def _seleccionar(df: pd.DataFrame):
    faltan = sorted(set(NUMERICAS + CATEGORICAS) - set(df.columns))
    if faltan:
        raise ValueError(f"Faltan campos requeridos para clusterizar: {faltan}")
    numericas = df[NUMERICAS].astype(float).copy()
    for columna in MONTOS:
        numericas[columna] = np.log1p(numericas[columna].clip(lower=0))
    numericas = numericas.replace([np.inf, -np.inf], np.nan)
    numericas = numericas.fillna(numericas.median()).to_numpy(dtype=np.float64)
    categoricas = df[CATEGORICAS].fillna("sin_dato").astype(str).to_numpy(dtype=object)
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
    minimo = x[train_indices].min(axis=0)
    maximo = x[train_indices].max(axis=0)
    rangos = np.where(maximo > minimo, maximo - minimo, 1.0)
    return x, minimo, rangos


def _gower(a_num, a_cat, b_num, b_cat, minimo, rangos):
    n_features = a_num.shape[1] + a_cat.shape[1]
    distancia = np.zeros((len(a_num), len(b_num)), dtype=np.float32)
    for j in range(a_num.shape[1]):
        diferencia = np.abs(a_num[:, None, j] - b_num[None, :, j]) / rangos[j]
        distancia += np.minimum(diferencia, 1.0).astype(np.float32)
    for j in range(a_cat.shape[1]):
        distancia += (a_cat[:, None, j] != b_cat[None, :, j]).astype(np.float32)
    return distancia / n_features


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


def comparar_clusterizaciones(
    df: pd.DataFrame,
    k_values=(3, 4, 5, 6),
    seed=42,
    gower_train_size=1800,
    evaluation_size=800,
    pam_starts=20,
    pam_max_iter=50,
):
    """Ajusta tres métodos y compara silhouette Gower en una evaluación común.

    K-Prototypes y K-Means mixto se ajustan con los perfiles fuera de la muestra
    común de evaluación. Gower + PAM usa una muestra acotada por su coste
    cuadrático. Todos se evalúan sobre los mismos perfiles con distancia Gower.
    """
    numericas, categoricas = _seleccionar(df)
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

    # Transformación común de valores monetarios para la distancia Gower.
    gower_num, minimo, rangos = _preparar_gower(numericas, train_idx)
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
