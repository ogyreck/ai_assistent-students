# StudAssis - Frontend

Vue 3 + TypeScript приложение для студенческого ассистента.

## Конфигурация API

API endpoints настраиваются в одном месте через переменные окружения:

1. Скопируйте `.env.example` в `.env`
2. Измените `VITE_API_BASE_URL` на адрес вашего бэкенда
3. Все API endpoints определены в `src/config/api.ts`

### Пример использования API:

```typescript
import apiClient from '@/utils/api'
import API_CONFIG from '@/config/api'

// GET запрос
const projects = await apiClient.get(API_CONFIG.endpoints.projects.list)

// POST запрос
const newProject = await apiClient.post(API_CONFIG.endpoints.projects.create, {
  name: 'Новый проект'
})
```

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd) 
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Type Support for `.vue` Imports in TS

TypeScript cannot handle type information for `.vue` imports by default, so we replace the `tsc` CLI with `vue-tsc` for type checking. In editors, we need [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) to make the TypeScript language service aware of `.vue` types.

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).

## Project Setup

```sh
npm install
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Type-Check, Compile and Minify for Production

```sh
npm run build
```

### Lint with [ESLint](https://eslint.org/)

```sh
npm run lint
```
