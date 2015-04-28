from web.models import Employee
for e in Employee.objects.all():
    print e["id"], e["name"], e["age"]