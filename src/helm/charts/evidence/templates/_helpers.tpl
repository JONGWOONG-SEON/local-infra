{{- define "evidence.name" -}}
{{ .Chart.Name }}
{{- end }}

{{- define "evidence.fullname" -}}
{{ include "evidence.name" . }}-{{ .Release.Name }}
{{- end }}