import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Import data from CSV files"

    CSV_FILES_MAP = {
        Ingredient: "ingredients.csv",
    }

    EXPECTED_FIELDS = {"name", "measurement_unit"}

    def add_arguments(self, parser):
        parser.add_argument(
            "--directory",
            type=str,
            default=settings.CSV_DIR,
            help="Path to the directory containing CSV files.",
        )

    def handle(self, *args, **options):
        csv_directory = options["directory"]

        for model in self.CSV_FILES_MAP.keys():
            self.import_data(model, csv_directory)

        self.stdout.write(
            self.style.SUCCESS(
                "✅ All data imported successfully."
            )
        )

    def import_data(self, model, csv_directory):
        csv_filename = self.CSV_FILES_MAP[model]
        file_path = os.path.join(csv_directory, csv_filename)
        self.verify_file_exists(file_path)

        self.stdout.write(
            self.style.NOTICE(
                f"📥 Importing data from: {file_path}..."
            )
        )

        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            self.validate_csv_fields(reader.fieldnames)

            created_count = 0
            skipped_count = 0

            for data in reader:
                obj, created = model.objects.get_or_create(
                    name=data["name"],
                    measurement_unit=data["measurement_unit"],
                )
                if created:
                    created_count += 1
                else:
                    skipped_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Imported {created_count} new records. "
                    f"Skipped {skipped_count} existing records."
                )
            )

    def clear_existing_data(self, model):
        model.objects.all().delete()

    def verify_file_exists(self, file_path):
        if not os.path.isfile(file_path):
            raise CommandError(f"❌ Error: File {file_path} not found.")

    def validate_csv_fields(self, fieldnames):
        if set(fieldnames) != self.EXPECTED_FIELDS:
            raise CommandError(
                "❌ Error: Invalid file format: incorrect field headers."
            )
