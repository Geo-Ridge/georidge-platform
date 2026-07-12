from dataclasses import dataclass, field

from georidge_platform.apps.qgis_server.services import (
    validate_on_server,
    get_extent_via_server,
)


@dataclass
class ValidationReport:
    valid: bool = True
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    layer_count: int = 0
    broken_layers: list = field(default_factory=list)

    def to_dict(self):
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "layer_count": self.layer_count,
            "broken_layers": self.broken_layers,
        }


def validate_project(project_path, project=None):
    report = ValidationReport()
    extent = None

    if project is None:
        report.warnings.append("No project provided — cannot validate.")
        report.valid = False
        return report

    server_result = validate_on_server(project)
    report.valid = server_result["valid"]
    report.errors = server_result["errors"]
    report.layer_count = server_result["layer_count"]

    if report.valid:
        try:
            extent = get_extent_via_server(project)
        except Exception as e:
            report.warnings.append(f"Extent extraction failed: {str(e)}")

    if extent is not None:
        try:
            project.extent_min_x = extent[0]
            project.extent_min_y = extent[1]
            project.extent_max_x = extent[2]
            project.extent_max_y = extent[3]
            project.save(update_fields=[
                "extent_min_x", "extent_min_y",
                "extent_max_x", "extent_max_y",
            ])
        except Exception as e:
            report.warnings.append(f"Extent save failed: {str(e)}")

    return report
