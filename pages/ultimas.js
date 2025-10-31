import React, { useState, useEffect, useMemo } from 'react';
import ResultList from '../components/ResultList';

/**
 * Página que muestra las últimas licitaciones publicadas.
 *
 * Carga todas las licitaciones activas y las ordena por fecha de
 * publicación descendente, mostrando las más recientes al inicio.
 */
export default function Ultimas() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/data/tenders-active.json`, {
          cache: 'no-store'
        });
        if (!res.ok) throw new Error('No se pudieron cargar los datos');
        const json = await res.json();
        setData(json);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const sorted = useMemo(() => {
    return data
      .slice()
      .sort((a, b) => {
        const dateA = new Date(a.fechaPublicacion || 0);
        const dateB = new Date(b.fechaPublicacion || 0);
        return dateB - dateA;
      })
      .slice(0, 50);
  }, [data]);

  return (
    <div className="max-w-5xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Últimas licitaciones</h1>
      <p className="mb-4">A continuación se muestran las licitaciones más recientes.</p>
      {loading && <p>Cargando datos…</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && <ResultList items={sorted} />}
    </div>
  );
}
