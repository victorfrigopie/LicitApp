import React, { useState, useEffect, useMemo } from 'react';
import ResultList from '../components/ResultList';

/**
 * Página principal de LicitApp.
 *
 * Muestra un buscador de licitaciones con filtros por texto, provincia
 * e importe mínimo. Los datos se cargan de forma dinámica desde
 * `/data/tenders-active.json`, que se genera automáticamente por
 * el script de sincronización.
 */
export default function Home() {
  const [data, setData] = useState([]);
  const [query, setQuery] = useState('');
  const [provincia, setProvincia] = useState('');
  const [minImporte, setMinImporte] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/data/tenders-active.json`, {
          cache: 'no-store'
        });
        if (!res.ok) {
          throw new Error('No se pudieron cargar los datos');
        }
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

  // Obtener lista única de provincias presentes en los datos
  const provincias = useMemo(() => {
    const set = new Set();
    data.forEach((lic) => {
      if (lic.provincia) set.add(lic.provincia);
      else if (lic.ccaa) set.add(lic.ccaa);
    });
    return Array.from(set).sort();
  }, [data]);

  // Filtrar resultados según query, provincia e importe mínimo
  const filtered = useMemo(() => {
    return data
      .filter((lic) => {
        // Filtrar por provincia si está seleccionada
        if (provincia) {
          const loc = (lic.provincia || lic.ccaa || '').toLowerCase();
          if (!loc.includes(provincia.toLowerCase())) return false;
        }
        // Filtrar por importe mínimo
        if (minImporte) {
          const imp = lic.importe || 0;
          if (imp < parseFloat(minImporte)) return false;
        }
        // Filtrar por query en título, órgano o CPV
        if (query) {
          const q = query.toLowerCase();
          const inFields =
            (lic.titulo && lic.titulo.toLowerCase().includes(q)) ||
            (lic.organo && lic.organo.toLowerCase().includes(q)) ||
            (lic.cpv && lic.cpv.toLowerCase().includes(q));
          if (!inFields) return false;
        }
        return true;
      })
      .sort((a, b) => {
        // Ordenar por fecha límite ascendente (las más próximas primero)
        const dateA = new Date(a.fechaLimite || a.fechaPublicacion || 0);
        const dateB = new Date(b.fechaLimite || b.fechaPublicacion || 0);
        return dateA - dateB;
      });
  }, [data, query, provincia, minImporte]);

  return (
    <div className="max-w-5xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">LicitApp</h1>
      <p className="mb-4">
        Busca y filtra licitaciones públicas de España de manera gratuita. Introduce
        palabras clave o selecciona una provincia para empezar.
      </p>
      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <input
          type="text"
          placeholder="Buscar..."
          className="border p-2 rounded w-full"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className="border p-2 rounded w-full"
          value={provincia}
          onChange={(e) => setProvincia(e.target.value)}
        >
          <option value="">Todas las provincias</option>
          {provincias.map((prov) => (
            <option key={prov} value={prov}>
              {prov}
            </option>
          ))}
        </select>
        <input
          type="number"
          min="0"
          placeholder="Importe mínimo (€)"
          className="border p-2 rounded w-full"
          value={minImporte}
          onChange={(e) => setMinImporte(e.target.value)}
        />
      </div>
      {loading && <p>Cargando datos…</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && <ResultList items={filtered} />}
    </div>
  );
}
