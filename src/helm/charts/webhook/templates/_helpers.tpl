{{- define "webhook.name" -}}
{{ .Chart.Name }}
{{- end }}

{{- define "webhook.fullname" -}}
{{ include "webhook.name" . }}-{{ .Release.Name }}
{{- end }}