{{ fullname | escape | underline }}

.. automodule:: {{ fullname }}
   :no-members:

{% block attributes %}
{%- if attributes %}
.. rubric:: Module attributes

.. autosummary::
{% for item in attributes %}
   {{ item }}
{%- endfor %}
{% endif %}
{%- endblock %}

{% block functions %}
{%- if functions %}
.. rubric:: Functions

.. autosummary::
   :nosignatures:
{% for item in functions %}
   {{ item }}
{%- endfor %}
{% endif %}
{%- endblock %}

{% block classes %}
{%- if classes %}
.. rubric:: Classes

.. autosummary::
   :toctree:
   :nosignatures:
{% for item in classes %}
   {{ item }}
{%- endfor %}
{% endif %}
{%- endblock %}

{% block exceptions %}
{%- if exceptions %}
.. rubric:: Exceptions

.. autosummary::
   :toctree:
{% for item in exceptions %}
   {{ item }}
{%- endfor %}
{% endif %}
{%- endblock %}

{%- if functions %}
.. rubric:: Function details

{% for item in functions %}
.. autofunction:: {{ item }}
{%- endfor %}
{% endif %}

{%- if attributes %}
.. rubric:: Attribute details

{% for item in attributes %}
.. autodata:: {{ item }}
   :no-value:
{%- endfor %}
{% endif %}

{% block modules %}
{%- if modules %}
.. rubric:: Submodules

.. autosummary::
   :toctree:
   :recursive:
{% for item in modules %}
   {{ item }}
{%- endfor %}
{% endif %}
{%- endblock %}
