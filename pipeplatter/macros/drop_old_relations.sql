-- macros/drop_old_relations.sql
{% macro drop_relation_if_exists(relation_name, schema_name) %}
  {% set relation = api.Relation.create(database=target.database, schema=schema_name, identifier=relation_name) %}
  {% do run_query("DROP TABLE IF EXISTS " ~ relation) %}
{% endmacro %}