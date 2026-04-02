"""LCOM (Lack of Cohesion of Methods) metrics - 8 variants."""

from __future__ import annotations

from archunitpython.metrics.common.types import ClassInfo


class LCOM96a:
    """LCOM96a: (1/(1-m)) * ((1/a) * sum(mu(Ai)) - m)."""

    name = "LCOM96a"
    description = "Lack of Cohesion of Methods (96a variant)"

    def calculate(self, class_info: ClassInfo) -> float:
        m = len(class_info.methods)
        a = len(class_info.fields)
        if m <= 1 or a == 0:
            return 0.0

        total_mu = sum(len(f.accessed_by) for f in class_info.fields)
        return (1 / (1 - m)) * ((1 / a) * total_mu - m)


class LCOM96b:
    """LCOM96b: (1/a) * sum((1/m) * (m - mu(Ai))). Normalized to [0,1]."""

    name = "LCOM96b"
    description = "Lack of Cohesion of Methods (96b variant, 0-1 normalized)"

    def calculate(self, class_info: ClassInfo) -> float:
        m = len(class_info.methods)
        a = len(class_info.fields)
        if m == 0 or a == 0:
            return 0.0

        total = 0.0
        for field in class_info.fields:
            mu_a = len(field.accessed_by)
            total += (1 / m) * (m - mu_a)

        return total / a


class LCOM1:
    """LCOM1: |P| - |Q| where P = non-sharing pairs, Q = sharing pairs."""

    name = "LCOM1"
    description = "Lack of Cohesion of Methods (LCOM1)"

    def calculate(self, class_info: ClassInfo) -> float:
        methods = class_info.methods
        m = len(methods)
        if m <= 1:
            return 0.0

        p = 0  # Non-sharing pairs
        q = 0  # Sharing pairs

        for i in range(m):
            for j in range(i + 1, m):
                fields_i = set(methods[i].accessed_fields)
                fields_j = set(methods[j].accessed_fields)
                if fields_i & fields_j:
                    q += 1
                else:
                    p += 1

        return float(max(0, p - q))


class LCOM2:
    """LCOM2: 1 - (sum(MF) / (M * F)) where MF = methods accessing field f."""

    name = "LCOM2"
    description = "Lack of Cohesion of Methods (LCOM2)"

    def calculate(self, class_info: ClassInfo) -> float:
        m = len(class_info.methods)
        f = len(class_info.fields)
        if m == 0 or f == 0:
            return 0.0

        total_mf = sum(len(field.accessed_by) for field in class_info.fields)
        return 1 - (total_mf / (m * f))


class LCOM3:
    """LCOM3: (M - sum(MF)/F) / (M - 1)."""

    name = "LCOM3"
    description = "Lack of Cohesion of Methods (LCOM3)"

    def calculate(self, class_info: ClassInfo) -> float:
        m = len(class_info.methods)
        f = len(class_info.fields)
        if m <= 1 or f == 0:
            return 0.0

        total_mf = sum(len(field.accessed_by) for field in class_info.fields)
        return (m - total_mf / f) / (m - 1)


class LCOM4:
    """LCOM4: Number of connected components in method-field access graph."""

    name = "LCOM4"
    description = "Lack of Cohesion of Methods (LCOM4, connected components)"

    def calculate(self, class_info: ClassInfo) -> float:
        methods = class_info.methods
        if not methods:
            return 0.0

        # Build adjacency: two methods are connected if they share a field
        n = len(methods)
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py

        for i in range(n):
            for j in range(i + 1, n):
                fields_i = set(methods[i].accessed_fields)
                fields_j = set(methods[j].accessed_fields)
                if fields_i & fields_j:
                    union(i, j)

        components = len(set(find(i) for i in range(n)))
        return float(components)


class LCOM5:
    """LCOM5: (a - mu * sum(mA)) / (a - mu) adjusted by method count."""

    name = "LCOM5"
    description = "Lack of Cohesion of Methods (LCOM5)"

    def calculate(self, class_info: ClassInfo) -> float:
        m = len(class_info.methods)
        a = len(class_info.fields)
        if m <= 1 or a == 0:
            return 0.0

        total_mf = sum(len(field.accessed_by) for field in class_info.fields)
        avg_mf = total_mf / a if a > 0 else 0

        denominator = m - 1
        if denominator == 0:
            return 0.0

        return (m - avg_mf) / denominator


class LCOMStar:
    """LCOM* (Henderson-Sellers variant): based on method pair sharing ratio."""

    name = "LCOMStar"
    description = "Lack of Cohesion of Methods (Henderson-Sellers variant)"

    def calculate(self, class_info: ClassInfo) -> float:
        m = len(class_info.methods)
        a = len(class_info.fields)
        if m <= 1 or a == 0:
            return 0.0

        total_mu = sum(len(f.accessed_by) for f in class_info.fields)
        avg_mu = total_mu / a

        return (m - avg_mu) / (m - 1)
