"""Bounded MCP chart authoring against the registered CRM analytics datasets."""

import json
import re

from .bootstrap_superset import DATASETS, SupersetApi, count_metric, create_grid_position, sum_metric

MANAGED_DESCRIPTION = "Tạo qua CRM Superset MCP; nguồn analytics đã đăng ký."


class SupersetAuthoring:
    def __init__(self, url, username, password):
        self.api = SupersetApi(url, username, password)

    def list_datasets(self, include_columns=False):
        allowed = {name for name, _ in DATASETS}
        datasets = [item for item in self.api.list("dataset")
                if item.get("schema") == "analytics" and item.get("table_name") in allowed
                and (item.get("database") or {}).get("database_name") == "CRM Analytics"]
        result = [{"id": item["id"], "table_name": item["table_name"], "schema": "analytics"} for item in datasets]
        if include_columns:
            for item in result:
                detail = self.api._request(f"/api/v1/dataset/{item['id']}")["result"]
                item["columns"] = [{"name": col["column_name"], "type": col.get("type"),
                                    "is_datetime": col.get("is_dttm", False)} for col in detail.get("columns", [])]
        return result

    @staticmethod
    def _title(value):
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 150:
            raise ValueError("Tên cần có từ 1 đến 150 ký tự.")
        return value.strip()

    @staticmethod
    def _id(value):
        if type(value) is not int or value <= 0:
            raise ValueError("ID phải là số nguyên dương.")
        return value

    def create_chart(self, title, dataset_id, kind, group_by=None, metric="count", metric_column=None, replace_existing=False):
        title, dataset_id = self._title(title), self._id(dataset_id)
        if type(replace_existing) is not bool:
            raise ValueError("replace_existing phải là boolean.")
        if kind not in {"bar", "line", "pie", "table", "number"}:
            raise ValueError("Loại biểu đồ không được hỗ trợ.")
        if dataset_id not in {item["id"] for item in self.list_datasets()}:
            raise ValueError("Chỉ được dùng dataset analytics đã đăng ký cho CRM Analytics.")
        detail = self.api._request(f"/api/v1/dataset/{dataset_id}")["result"]
        columns = {col["column_name"]: col for col in detail["columns"]}
        if kind != "number" and (not isinstance(group_by, str) or group_by not in columns):
            raise ValueError("Cần chọn cột nhóm hợp lệ từ dataset.")
        if metric == "count":
            measure = count_metric()
        elif metric in {"sum", "avg", "min", "max"}:
            if not isinstance(metric_column, str) or metric_column not in columns:
                raise ValueError("Cột đo lường không tồn tại trong dataset.")
            col = columns[metric_column]
            if not re.search(r"INT|FLOAT|DOUBLE|DECIMAL|NUMERIC|REAL", str(col.get("type", "")), re.I):
                raise ValueError("Phép tổng hợp yêu cầu cột số.")
            measure = sum_metric(metric_column)
            measure["aggregate"] = metric.upper()
            if metric != "sum":
                measure["label"] = f"{metric.upper()}({metric_column})"
        else:
            raise ValueError("Chỉ hỗ trợ count, sum, avg, min và max.")
        viz = {"bar": "echarts_timeseries_bar", "line": "echarts_timeseries_line",
               "pie": "pie", "table": "table", "number": "big_number_total"}[kind]
        params = {"viz_type": viz, "datasource": f"{dataset_id}__table", "adhoc_filters": [],
                  "row_limit": 1000, "time_range": "No filter", "color_scheme": "supersetColors"}
        if kind in {"bar", "line"}:
            params.update({"x_axis": group_by, "metrics": [measure], "groupby": [], "show_legend": True})
        elif kind == "pie":
            params.update({"groupby": [group_by], "metric": measure, "show_legend": True,
                           "order_desc": True, "label_type": "key_value"})
        elif kind == "table":
            params.update({"groupby": [group_by], "metrics": [measure], "query_mode": "aggregate"})
        else:
            params["metric"] = measure
        payload = {"slice_name": title, "datasource_id": dataset_id, "datasource_type": "table",
                   "viz_type": viz, "params": json.dumps(params),
                   "description": MANAGED_DESCRIPTION}
        for existing in self.api.list("chart"):
            if existing.get("slice_name") == title:
                saved = self.api._request(f"/api/v1/chart/{existing['id']}")["result"]
                if (saved.get("datasource_id") == dataset_id
                        and json.loads(saved.get("params") or "{}") == params):
                    return {"status": "SUCCESS", "id": existing["id"], "created": False}
                if (replace_existing and saved.get("datasource_id") == dataset_id
                        and saved.get("description") == MANAGED_DESCRIPTION):
                    self.api._request(f"/api/v1/chart/{existing['id']}", "PUT", payload)
                    return {"status": "SUCCESS", "id": existing["id"], "created": False, "updated": True}
                raise ValueError("Tên biểu đồ đã có cấu hình khác; dùng tên mới để giữ nguyên biểu đồ cũ.")
        saved = self.api._request("/api/v1/chart/", "POST", payload)
        chart_id = saved.get("id") or saved["result"]["id"]
        return {"status": "SUCCESS", "id": chart_id, "created": True,
                "url": f"{self.api.base_url}/explore/?slice_id={chart_id}"}

    def create_dashboard(self, title, slug, chart_ids, published=False):
        title = self._title(title)
        if not isinstance(slug, str) or not re.fullmatch(r"crm-mcp-[a-z0-9]+(?:-[a-z0-9]+)*", slug) or len(slug) > 100:
            raise ValueError("Slug phải bắt đầu crm-mcp- và chỉ có chữ thường, số, dấu gạch nối.")
        if not isinstance(chart_ids, list) or not 1 <= len(chart_ids) <= 12:
            raise ValueError("Dashboard cần từ 1 đến 12 biểu đồ.")
        ids = [self._id(value) for value in chart_ids]
        if len(set(ids)) != len(ids) or type(published) is not bool:
            raise ValueError("Danh sách biểu đồ không được trùng và published phải là boolean.")
        dataset_ids = {item["id"] for item in self.list_datasets()}
        details = [self.api._request(f"/api/v1/chart/{chart_id}")["result"] for chart_id in ids]
        if any(item.get("datasource_id") not in dataset_ids or item.get("datasource_type") != "table" for item in details):
            raise ValueError("Dashboard chỉ được chứa biểu đồ từ dataset CRM analytics.")
        existing = next((item for item in self.api.list("dashboard") if item.get("slug") == slug), None)
        if existing:
            dashboard_id = existing["id"]
            saved = self.api._request(f"/api/v1/dashboard/{dashboard_id}")["result"]
            position = json.loads(saved.get("position_json") or "{}")
            stored_ids = {item.get("meta", {}).get("chartId") for item in position.values() if isinstance(item, dict) and item.get("type") == "CHART"}
            if stored_ids != set(ids) or saved.get("dashboard_title") != title or saved.get("published") != published:
                raise ValueError("Dashboard đã có cấu hình khác; dùng slug mới để không ghi đè thay đổi thủ công.")
        else:
            payload = {"dashboard_title": title, "slug": slug, "published": published,
                       "position_json": json.dumps(create_grid_position(ids, self.api)),
                       "json_metadata": json.dumps({"timed_refresh_immune_slices": [], "expanded_slices": {}})}
            saved = self.api._request("/api/v1/dashboard/", "POST", payload)
            dashboard_id = saved.get("id") or saved["result"]["id"]
        # Preserve memberships in every existing dashboard, including shared charts.
        for chart_id, detail in zip(ids, details):
            memberships = {item["id"] if isinstance(item, dict) else item for item in detail.get("dashboards", [])}
            if dashboard_id not in memberships:
                self.api._request(f"/api/v1/chart/{chart_id}", "PUT", {"dashboards": sorted(memberships | {dashboard_id})})
        return {"status": "SUCCESS", "id": dashboard_id, "created": existing is None,
                "published": published, "url": f"{self.api.base_url}/superset/dashboard/{slug}/"}
