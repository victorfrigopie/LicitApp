import React from 'react';

/**
 * Componente para mostrar una lista de licitaciones.
 *
 * Recibe un array de objetos licitación y los renderiza en
 * una tabla simple. Cada fila muestra el título, el órgano
 * de contratación, la provincia, la fecha límite y un enlace.
 */
export default function ResultList({ items }) {
  if (!items || items.length === 0) {
    return <p>No se encontraron licitaciones que coincidan con tu búsqueda.</p>;
  }
  return (
    <table className="min-w-full text-sm table-auto border-collapse">
      <thead>
        <tr className="bg-gray-200">
          <th className="px-2 py-1 text-left">Título</th>
          <th className="px-2 py-1 text-left">Órgano</th>
          <th className="px-2 py-1 text-left">Provincia</th>
          <th className="px-2 py-1 text-left">Límite</th>
          <th className="px-2 py-1 text-left">Enlace</th>
        </tr>
      </thead>
      <tbody>
        {items.map((lic) => (
          <tr key={lic.id} className="border-b">
            <td className="px-2 py-1 max-w-xs truncate" title={lic.titulo}>{lic.titulo}</td>
            <td className="px-2 py-1" title={lic.organo}>{lic.organo}</td>
            <td className="px-2 py-1">{lic.provincia || lic.ccaa}</td>
            <td className="px-2 py-1">{lic.fechaLimite || '-'}</td>
            <td className="px-2 py-1 text-blue-600 underline">
              {lic.enlace ? (
                <a href={lic.enlace} target="_blank" rel="noopener noreferrer">
                  Ver
                </a>
              ) : (
                '-'
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
