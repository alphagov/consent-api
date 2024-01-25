import secrets
import string
import subprocess
from dataclasses import dataclass

import pulumi
from pulumi_gcp import sql

from resources import AbstractResource


@dataclass
class Database(AbstractResource):
    def _create(self) -> None:
        self.db_deletion_protected = (
            pulumi.Config("sde-consent-api").require("db-deletion-protected") == "true"
        )

        self.db_instance = sql.DatabaseInstance(
            f"{self.config.stack}-db-instance",
            database_version=pulumi.Config().require("db-version"),
            deletion_protection=self.db_deletion_protected,
            settings={"tier": pulumi.Config().require("db-tier")},
        )

        self.db = sql.Database(
            self.resource_name("$--db", self.config.stack),
            name=self.config.stack,
            instance=self.db_instance.name,
        )

        self.db_user = sql.User(
            self.resource_name("$--db-user", self.config.stack),
            name=self.config.stack,
            instance=self.db_instance.name,
            password=self.generate_password(),
        )

        self.connection_name = self.db_instance.connection_name

        self.db_url: pulumi.Output = pulumi.Output.secret(
            pulumi.Output.format(
                "{dialect}://{user}:{password}@/{db}?host=/cloudsql/{connection}",
                dialect="postgresql+asyncpg",
                user=self.db_user.name,
                password=self.db_user.password,
                db=self.db.name,
                connection=self.connection_name,
            )
        )

    def get_db_instance_id(self, env: str) -> str:
        """Get an existing database instance in the given environment (if one
        exists)."""
        try:
            result = subprocess.run(
                [
                    "gcloud",
                    "sql",
                    "instances",
                    "list",
                    "--project",
                    "sde-consent-api",
                    "--format",
                    "value(name)",
                    "--filter",
                    f"name:{env}-*",
                ],
                check=True,
                stderr=subprocess.STDOUT,
                stdout=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as err:
            print("Failed getting existing database instance")
            print(f"{err.returncode=}")
            print(err.output)
            raise
        return result.stdout.strip()

    def generate_password(self, length: int = 20) -> pulumi.Output[str]:
        """Generate a random password."""
        alphabet = string.ascii_letters + string.digits
        return pulumi.Output.secret(
            "".join(secrets.choice(alphabet) for i in range(length)),
        )
