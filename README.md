# LicitApp

LicitApp es una plataforma gratuita para consultar y filtrar licitaciones públicas de España. Esta aplicación utiliza los datos abiertos de la Plataforma de Contratación del Sector Público (PLACSP) y un chat basado en IA para ayudarte a encontrar licitaciones de tu interés.

## Descripción del proyecto

Este repositorio contiene un sitio web construido con Next.js y una serie de scripts Python para sincronizar datos de licitaciones y enviar alertas a los usuarios.

### Estructura

- `scripts/placsp_sync.py`: Sincroniza los datos de la PLACSP generando archivos JSON con licitaciones actuales e históricas.
- `scripts/enviar_alertas.py`: Envía correos electrónicos a suscriptores cuando hay licitaciones que coinciden con sus criterios.
- `scripts/requirements.txt`: Dependencias de Python para los scripts.
- `pages/`: Contiene las páginas del sitio Next.js (`index.js`, `ultimas.js`, `suscribirse.js`).
- `components/ResultList.js`: Componente de React para mostrar licitaciones en una tabla.
- `data/`: Datos generados (`tenders-active.json`, `tenders.ndjson`, `subscribers.json`).
- `.github/workflows/sync.yml`: Workflow de GitHub Actions para sincronizar datos y enviar alertas.
- `.github/workflows/deploy.yml`: Workflow de despliegue para GitHub Pages (para construir y publicar la web).
- `next.config.js`: Configuración de Next.js para exportar el sitio estático.
- `package.json`: Dependencias y scripts de Node/Next.js.

## Uso

1. Instala las dependencias del proyecto:

   ```bash
   npm install
   ```

2. Ejecuta el modo desarrollo de Next.js:

   ```bash
   npm run dev
   ```

3. Para generar la versión estática que se despliega en GitHub Pages:

   ```bash
   npm run build && npm run export
   ```

   El resultado se genera en la carpeta `out/`. Los datos de licitaciones se copian en `out/data/` durante el despliegue.

## Licencia

Este proyecto se distribuye bajo la licencia MIT.
