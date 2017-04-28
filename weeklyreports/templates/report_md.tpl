## Week of {{ week_of }}
{% if link -%}
[Open in google docs](https://docs.google.com/document/d/{{ link }})
{% endif -%}
{% for report in reports -%}{% for topic, summaries in report.iteritems() %}

### {{ topic }}

{% for summary in summaries %}
{% if summary|isWhiteSpace -%}
{{ summary -}}
{% else -%}
- {{ summary -}}
{% endif -%}
{% endfor %}{% endfor %}{% endfor %}
