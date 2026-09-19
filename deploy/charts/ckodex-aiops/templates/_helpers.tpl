{{/*
Expand the name of the chart.
*/}}
{{- define "ckodex-aiops.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "ckodex-aiops.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ckodex-aiops.labels" -}}
helm.sh/chart: {{ include "ckodex-aiops.name" . }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "ckodex-aiops.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
ckodex.ai/assurance-level: {{ .Values.global.assuranceLevel | default "GAL-1" }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ckodex-aiops.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ckodex-aiops.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
