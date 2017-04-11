<!DOCTYPE html>
<html>
<head>
    <title>Flask Template Example</title>
</head>
<body>
<h2>Week of {{ week_of }}</h2>
{% if link %}
<a href="https://docs.google.com/document/d/{{ link }}">Open in google docs</a>
{% endif %}

{% for report in reports %}{% for topic, summaries in report.iteritems() %}
    <h3>{{ topic }}</h3>
    <ul>
    {% for summary in summaries %}
        {% if summary|isBulletItem %}
        <ul><li>{{ summary[2:] }}</li></ul>
        {% else %}
        <li>{{ summary }}</li>
        {% endif %}
    {% endfor %}
    </ul>
{% endfor %}{% endfor %}
</body>
</html>