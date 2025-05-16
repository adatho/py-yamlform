from pathlib import Path

import yaml
from flask import Flask, Response, render_template, request

app = Flask(__name__)

# Verzeichnis mit YAML-Dateien
FORMS_DIR = Path("forms")


# Alle YAML-Dateien aus dem Verzeichnis laden
def load_yaml_files():
    forms = {}
    for file in FORMS_DIR.glob("*.yaml"):
        with open(file, "r") as f:
            forms[file.stem] = yaml.safe_load(f)
    return forms


# Beim Start alle YAML-Dateien einlesen
forms_definitions = load_yaml_files()


@app.route("/")
def select_form():
    # Liste der verfügbaren YAML-Dateien
    forms = [(key, forms_definitions[key]["title"]) for key in forms_definitions]
    return render_template("select_form.html", forms=forms)


@app.route("/form/<form_key>", methods=["GET", "POST"])
def show_form(form_key):
    form_def = forms_definitions.get(form_key)
    if not form_def:
        return "Form not found", 404

    vars_def = form_def["variables"]

    if request.method == "POST":
        result = {"form": form_key, "variables": []}
        for v in vars_def:
            name = v["name"]
            t = v["type"]
            if t == "boolean":
                val = name in request.form
            elif t == "number":
                val = request.form.get(name, type=float)
            elif t == "map":
                sub = {}
                for k in v["default"]:
                    keyname = f"{name}[{k}]"
                    sub[k] = request.form.get(keyname)
                val = sub
            elif t == "range":
                start = request.form.get(f"{name}[start]", type=int)
                end = request.form.get(f"{name}[end]", type=int)
                val = {"start": start, "end": end}
            else:
                val = request.form.get(name)
            result["variables"].append({"name": name, "value": val})

        out_yaml = yaml.safe_dump(
            {"form": form_key, "values": result["variables"]},
            sort_keys=False,
            allow_unicode=True,
        )
        return render_template("result.html", out_yaml=out_yaml, form_key=form_key)

    return render_template(
        "form.html", form_key=form_key, title=form_def["title"], variables=vars_def
    )


@app.route("/download/<form_key>", methods=["POST"])
def download_yaml(form_key):
    yaml_data = request.form["yaml_data"]
    response = Response(yaml_data, mimetype="text/yaml")
    response.headers["Content-Disposition"] = f"attachment; filename={form_key}.yaml"
    return response


if __name__ == "__main__":
    app.run(debug=True)
