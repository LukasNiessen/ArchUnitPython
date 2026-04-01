"""Robert C. Martin's distance metrics: Abstractness, Instability, Distance."""

from __future__ import annotations

from dataclasses import dataclass

from archunitpy.metrics.common.types import FileAnalysisResult


@dataclass
class DistanceMetrics:
    """Distance metrics for a file/module."""

    abstractness: float  # A = Na / N
    instability: float  # I = Ce / (Ca + Ce)
    distance: float  # D = |A + I - 1|
    coupling_factor: float  # CF
    normalized_distance: float
    in_zone_of_pain: bool
    in_zone_of_uselessness: bool


@dataclass
class ProjectDistanceMetrics:
    """Project-wide distance metric summary."""

    average_abstractness: float
    average_instability: float
    average_distance: float
    files_in_zone_of_pain: int
    files_in_zone_of_uselessness: int
    total_files: int


def calculate_file_distance_metrics(
    file_analysis: FileAnalysisResult,
    all_files: list[FileAnalysisResult],
) -> DistanceMetrics:
    """Calculate distance metrics for a single file.

    Args:
        file_analysis: Analysis result for the target file.
        all_files: All file analysis results (for coupling calculation).
    """
    # Abstractness: ratio of abstract types to total types
    total_types = file_analysis.total_types
    abstract_types = file_analysis.abstract_classes + file_analysis.protocols

    abstractness = abstract_types / total_types if total_types > 0 else 0.0

    # Coupling: count files that depend on this file (Ca) and
    # files this file depends on (Ce)
    # For simplicity, use class count as proxy for coupling
    ce = sum(c.efferent_coupling for c in file_analysis.classes)
    ca = sum(c.afferent_coupling for c in file_analysis.classes)
    total_coupling = ca + ce

    instability = ce / total_coupling if total_coupling > 0 else 0.5

    # Distance from main sequence
    distance = abs(abstractness + instability - 1)

    # Coupling factor
    max_coupling = max(1, len(all_files) - 1) * 2
    coupling_factor = total_coupling / max_coupling if max_coupling > 0 else 0.0

    # Normalized distance
    normalized_distance = distance

    # Zone detection
    in_zone_of_pain = abstractness < 0.25 and instability < 0.25
    in_zone_of_uselessness = abstractness > 0.75 and instability > 0.75

    return DistanceMetrics(
        abstractness=abstractness,
        instability=instability,
        distance=distance,
        coupling_factor=coupling_factor,
        normalized_distance=normalized_distance,
        in_zone_of_pain=in_zone_of_pain,
        in_zone_of_uselessness=in_zone_of_uselessness,
    )


def calculate_distance_metrics_for_project(
    files: list[FileAnalysisResult],
) -> ProjectDistanceMetrics:
    """Calculate project-wide distance metric summary."""
    if not files:
        return ProjectDistanceMetrics(
            average_abstractness=0,
            average_instability=0,
            average_distance=0,
            files_in_zone_of_pain=0,
            files_in_zone_of_uselessness=0,
            total_files=0,
        )

    metrics = [calculate_file_distance_metrics(f, files) for f in files]

    return ProjectDistanceMetrics(
        average_abstractness=sum(m.abstractness for m in metrics) / len(metrics),
        average_instability=sum(m.instability for m in metrics) / len(metrics),
        average_distance=sum(m.distance for m in metrics) / len(metrics),
        files_in_zone_of_pain=sum(1 for m in metrics if m.in_zone_of_pain),
        files_in_zone_of_uselessness=sum(
            1 for m in metrics if m.in_zone_of_uselessness
        ),
        total_files=len(files),
    )
