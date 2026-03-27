import { jsx as _jsx } from "react/jsx-runtime";
import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import { App } from "./App";
var rootElement = document.getElementById("root");
if (!rootElement) {
    throw new Error("Root element #root not found");
}
ReactDOM.createRoot(rootElement).render(_jsx(React.StrictMode, { children: _jsx(App, {}) }));
