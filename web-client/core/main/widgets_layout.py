# Copyright INRIM (https://www.inrim.eu)
# See LICENSE file for full licensing details.
import sys
from copy import deepcopy
import logging
import ujson
from fastapi.templating import Jinja2Templates

from .builder_custom import *
from .widgets_content import PageWidget
from .base.base_class import BaseClass, PluginBase

logger = logging.getLogger(__name__)


class LayoutWidget(PluginBase):
    plugins = []

    def __init_subclass__(cls, **kwargs):
        if cls not in cls.plugins:
            cls.plugins.append(cls())


class LayoutWidgetBase(LayoutWidget, PageWidget):
    @classmethod
    def create(
        cls,
        templates_engine,
        session,
        request,
        settings,
        content,
        schema={},
        **kwargs
    ):
        self = LayoutWidgetBase()
        self.init(
            templates_engine,
            session,
            request,
            settings,
            content,
            schema,
            **kwargs
        )
        return self

    def init(
        self,
        templates_engine,
        session,
        request,
        settings,
        content,
        schema,
        **kwargs
    ):
        self.settings = settings
        self.content = deepcopy(content)
        disabled = not self.content.get("editable")
        super().init(
            templates_engine,
            session,
            request,
            settings,
            disabled=disabled,
            **kwargs
        )
        self.page_config = content
        self.schema = schema
        self.cls_title = " text-center "
        self.curr_row = []
        self.submission_id = ""
        self.context = kwargs.get("context", {})
        self.breadcrumb = kwargs.get("breadcrumb", [])
        self.form_name = ""
        self.rec_name = self.schema.get("rec_name")
        self.form_data = {}
        self.form_data_values = {}
        self.context_buttons = []
        self.agent = request.headers.get("User-Agent").lower()
        # self.init_layout()
        # logger.info(f"LayoutWidget init complete {self.security_headers}")

    def init_layout(self):
        self.title = self.schema["title"]
        self.name = self.schema["rec_name"]
        self.form_id = self.schema["_id"]
        self.sys_component = self.schema["sys"]
        self.handle_global_change = (
            int(self.schema.get("handle_global_change", 0)) == 1
        )
        self.no_cancel = int(self.schema.get("no_cancel", 0)) == 1
        self.builder_mode = self.session.get("app", {}).get("builder", False)
        self.builder = CustomBuilder(
            self.schema.copy(),
            template_engine=self.tmpe,
            disabled=self.disabled,
            settings=self.settings,
            context=self.context,
            authtoken=self.authtoken,
            theme_cfg=self.theme_cfg,
            is_mobile=self.is_mobile,
            security_headers=self.security_headers,
            form_data={},
        )
        if self.is_admin and self.builder_mode:
            self.make_menu()
        self.make_layout()

    def make_menu(self):
        logger.debug("make_menu")
        self.menu_headers = []
        menus = self.page_config.get("menu")
        for item in menus:
            for k, v in item.items():
                cfg = {
                    "key": k,
                    "label": k,
                    "items": v,
                }
                self.menu_headers.append(
                    self.render_custom(
                        self.theme_cfg.get_template("components", "menu"),
                        cfg.copy(),
                    )
                )

    def make_context_button(self, content):
        logger.debug("make_context_button")
        self.context_buttons = []
        buttons = content.get("context_buttons")
        if buttons:
            for item in buttons:
                if (
                    not (content.get("builder") and content["mode"] == "form")
                    and item
                ):
                    if (
                        not content.get("builder")
                        and item.get("builder")
                        and item.get("btn_action_type")
                    ):
                        pass
                    else:
                        cfg = item.copy()
                        cfg["customClass"] = "col"
                        self.context_buttons.append(
                            self.render_custom(
                                self.theme_cfg.get_template(
                                    "components", "ctxbuttonaction"
                                ),
                                cfg,
                            )
                        )
        if self.context_buttons:
            row_cfg = {
                "customClass": "container",
                "rows": self.context_buttons,
            }
            self.beforerows.append(
                self.render_custom(
                    self.theme_cfg.get_template("components", "blockcolumns"),
                    row_cfg,
                )
            )

    def get_component_by_key(self, key):
        return self.builder.get_component_by_key(key)

    def make_layout(self):
        pass

    def prepare_render(self):
        template = self.theme_cfg.get_template(
            "components", self.builder.main.type
        )
        values = {
            "rows": self.rows,
            "base": self.theme_cfg.get_page_template("base"),
            "header": self.theme_cfg.get_page_template("header"),
            "title": self.title,
            "cls_title": self.cls_title,
            "label": self.label,
            "name": self.name,
            "rec_name": self.rec_name,
            "sys_form": self.sys_component,
            "menu_headers": self.menu_headers,
            "breadcrumb": self.breadcrumb,
            "user_menu_items": [],
            "builder_mode": self.session.get("app", {}).get("builder", False),
        }

        if self.is_admin:
            builde_toggle_item = self.render_custom(
                self.theme_cfg.get_template("components", "checkbox"),
                {
                    "key": "builder_mode",
                    "value": self.session.get("app").get("builder"),
                    "authtoken": self.authtoken,
                    "req_id": self.req_id,
                    "label": "Builder",
                    "custom_action": True,
                },
            )
            values["user_menu_items"].append(builde_toggle_item)
        return template, values

    def render_layout(self):
        # template = f"{self.components_base_path}{form_component_map[self.builder.main.type]}"
        template, values = self.prepare_render()
        return self.render_page(template, values)
