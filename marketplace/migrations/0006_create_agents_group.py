from django.db import migrations


AGENT_PERMISSION_CODENAMES = {
    # Core marketplace catalog management
    "add_car", "change_car", "delete_car", "view_car",
    "add_carimage", "change_carimage", "delete_carimage", "view_carimage",
    "add_phone", "change_phone", "delete_phone", "view_phone",
    "add_phoneimage", "change_phoneimage", "delete_phoneimage", "view_phoneimage",
    "add_accessory", "change_accessory", "delete_accessory", "view_accessory",
    "add_realestate", "change_realestate", "delete_realestate", "view_realestate",
    "add_realestateimage", "change_realestateimage", "delete_realestateimage", "view_realestateimage",
    # Inbound seller requests/proposals handling
    "add_proposal", "change_proposal", "delete_proposal", "view_proposal",
    "add_proposalimage", "change_proposalimage", "delete_proposalimage", "view_proposalimage",
    "add_carsellrequest", "change_carsellrequest", "delete_carsellrequest", "view_carsellrequest",
    "add_carsellrequestimage", "change_carsellrequestimage", "delete_carsellrequestimage", "view_carsellrequestimage",
}


def create_agents_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    agents_group, _ = Group.objects.get_or_create(name="Agents")

    permissions = Permission.objects.filter(
        content_type__app_label="marketplace",
        codename__in=AGENT_PERMISSION_CODENAMES,
    )
    agents_group.permissions.set(permissions)


def delete_agents_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Agents").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0005_car_slug_phone_slug_realestate_slug"),
    ]

    operations = [
        migrations.RunPython(create_agents_group, delete_agents_group),
    ]
