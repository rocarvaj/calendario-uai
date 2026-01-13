# Calendario académico UAI

[Calendario 2026 (versión web)](https://outlook.office365.com/calendar/published/a49ef94bcbad4479aa027b8b18e523b9@uai.cl/10216625fe1c40fb998efdf3ad73b3959654618250573524838/calendar.html)

Este repositorio contiene el calendario académico de la Universidad Adolfo Ibáñez en formato iCalendar (.ics), para importarlo en tu calendario personal y tener una vista más clara de los eventos.

Para importar el calendario a tu calendario personal, usa el archivo `calendario-academico-uai-XXXX.ics` (con el año más reciente) y las siguientes instrucciones:

- [En Google Calendar](https://support.google.com/calendar/answer/37118?hl=es&co=GENIE.Platform%3DDesktop).
- [En Outlook](https://support.microsoft.com/es-es/office/importar-calendarios-a-outlook-8e8364e1-400e-4c0f-a573-fe76b5a2d379)).


## Extracción de eventos

El script `extrae-cal-uai.py` es utilizado para procesar el calendario original (en formato PDF) y extraer los eventos. Para ejecutarlo, se recomienda el uso de [uv](https://docs.astral.sh/uv/):

```
uv run extrae-cal-uai.py calendario-academico-uai-2026.pdf
```


Rodolfo Carvajal, 2026
