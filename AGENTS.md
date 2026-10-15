# Instrucciones para agentes

Antes de cambiar el repositorio, lee `.codex/context/project.md` y `.codex/context/constraints.md`. Para tareas amplias, usa el flujo de `.codex/orchestration/WORKFLOW.md`.

- El alcance funcional se define en `docs/requisitos.md` y `docs/historias-de-usuario.md`; consulta también `README.md` para decisiones pendientes.
- Conserva la separación entre servicios, sus bases de datos y sus contratos.
- No incluyas secretos, datos locales ni estado de Terraform en los cambios.
- No ejecutes pruebas ni añadas nuevas salvo que el usuario lo solicite; cuando pida verificación, usa los comandos de `.codex/orchestration/commands.md`.
- Resume cambios, verificaciones realizadas y limitaciones en la respuesta final.
