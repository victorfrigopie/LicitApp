import React from 'react';

/**
 * Página de suscripción a alertas.
 *
 * Incluye un formulario que envía los datos a Formspree. Actualiza la
 * URL en el atributo `action` con tu endpoint de Formspree para recibir
 * las solicitudes de suscripción.
 */
export default function Suscribirse() {
  return (
    <div className="max-w-xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Suscribirse a alertas</h1>
      <p className="mb-4">
        Introduce tu correo electrónico y tus preferencias para recibir un email diario con nuevas
        licitaciones que coincidan con tus intereses.
      </p>
      <form
        action="https://formspree.io/f/REEMPLAZAR_ID" // Reemplaza con tu endpoint de Formspree
        method="POST"
        className="space-y-4"
      >
        <div>
          <label className="block mb-1">Correo electrónico</label>
          <input
            type="email"
            name="email"
            required
            className="border p-2 rounded w-full"
          />
        </div>
        <div>
          <label className="block mb-1">
            Palabras clave (separadas por comas)
          </label>
          <input
            type="text"
            name="keywords"
            placeholder="ej. impresoras, limpieza, cámaras"
            className="border p-2 rounded w-full"
          />
        </div>
        <div>
          <label className="block mb-1">Provincia</label>
          <input
            type="text"
            name="provincia"
            placeholder="ej. Madrid"
            className="border p-2 rounded w-full"
          />
        </div>
        <div>
          <label className="block mb-1">Tipo de contrato</label>
          <input
            type="text"
            name="tipo"
            placeholder="ej. Obras, Suministros, Servicios"
            className="border p-2 rounded w-full"
          />
        </div>
        <div>
          <label className="block mb-1">Importe mínimo (€)</label>
          <input
            type="number"
            name="importeMin"
            min="0"
            className="border p-2 rounded w-full"
          />
        </div>
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Suscribirme
        </button>
      </form>
    </div>
  );
}
