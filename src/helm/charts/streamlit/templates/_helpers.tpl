{{- define "streamlit.name" -}}
{{ .Chart.Name }}
{{- end }}

{{- define "streamlit.fullname" -}}
{{ include "streamlit.name" . }}-{{ .Release.Name }}
{{- end }}