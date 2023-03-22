from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))

results_filename = "results.html"
results_template = environment.get_template("results.html")
context = {
    "city": "Murcia",  

    "date_1" : "2021-03-26", 
    "date_2" : "2021-04-20", 

    "conc_1" : 30, 
    "conc_2" : 70, 

    "img_1" : "tmp/Murcia_2021-03-26.jpeg",
    "img_2" : "tmp/Murcia_2021-04-20.jpeg",

    "prev" : "tmp/Murcia_2021-04-20.jpeg", 
    "next": "tmp/Murcia_2021-03-26.jpeg",
    }

with open(results_filename, mode="w", encoding="utf-8") as results:
    results.write(results_template.render(context))
    print(f"generated: {results_filename}")