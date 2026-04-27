# Guía de Contribución — DriverDrowsGuard 

## Setup inicial

```bash
git clone https://github.com/FrancoBenites24/ProyectoDesarrollo
cd ProyectoDesarrollo
pip install poetry pre-commit
poetry install
pre-commit install
cp .env.example .env
```

## Git Workflow

1. **Tomar el Issue** del tablero Kanban y moverlo a “In Progress”
2. **Crear branch** desde `develop`:
   ```bash
   git checkout develop && git pull
   git checkout -b feat/NUMERO-descripcion
   ```
3. **Desarrollar** con commits pequeños y descriptivos
4. **Push** y abrir PR hacia `develop` (NUNCA hacia `main`)
5. **CI** debe pasar (lint + tests)
6. **Dev 1** hace code review — mínimo 1 approval
7. **Squash and merge** → branch eliminada automáticamente

## Convención de Commits

```
feat(core): add TemporalAnalyzer with PERCLOS
fix(utils): handle ZeroDivisionError in illumination
chore(infra): add Dockerfile multi-stage
test(core): add unit tests for EAR window
docs(readme): add hardware requirements
```

## Ejecutar Tests

```bash
poetry run pytest                         # todos
poetry run pytest tests/unit/             # solo unitarios
poetry run pytest -v -k "test_perclos"    # test específico
poetry run black src/ tests/              # formatear
poetry run flake8 src/ tests/             # lint
```

## Definición de Done (cada Issue)

- [ ] `black`, `isort`, `flake8` pasan sin errores
- [ ] Tests escritos (≥70% cobertura del módulo)
- [ ] Sin `print()` en código de producción
- [ ] Type hints en todas las funciones públicas
- [ ] Docstrings (Google Style) en clases y métodos públicos
- [ ] PR revisada y aprobada por Franco (Dev 1)
- [ ] Issue cerrado en GitHub
