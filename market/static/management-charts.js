(() => {
  const source = document.getElementById("finance-series");
  if (!source) return;
  const points = JSON.parse(source.textContent);
  const namespace = "http://www.w3.org/2000/svg";
  function node(tag, attributes, text) {
    const item = document.createElementNS(namespace, tag);
    for (const [key, value] of Object.entries(attributes)) item.setAttribute(key, value);
    if (text !== undefined) item.textContent = text;
    return item;
  }
  function chart(id, fields, data = points) {
    const target = document.getElementById(id);
    if (!target) return;
    const width = 720;
    const height = 260;
    const peak = Math.max(1, ...data.flatMap((point) => fields.map((field) => point[field.key])));
    const maximum = fields[0].key === "companies" ? Math.ceil(peak / 4) * 4 : peak;
    const svg = node("svg", {viewBox: `0 0 ${width} ${height}`, "aria-hidden": "true"});
    for (let tick = 0; tick <= 4; tick++) {
      const y = 210 - tick * 45;
      svg.append(node("line", {x1: 65, x2: 710, y1: y, y2: y, stroke: "#d8e5e2"}));
      svg.append(node("text", {x: 60, y: y + 4, "text-anchor": "end", fill: "#425a67", "font-size": 12},
        new Intl.NumberFormat("pt-BR", {maximumFractionDigits: 0}).format(maximum * tick / 4)));
    }
    data.forEach((point, index) => {
      const x = 78 + index * (630 / Math.max(data.length, 1));
      fields.forEach((field, position) => {
        const barHeight = point[field.key] / maximum * 180;
        const bar = node("rect", {x: x + position * 14, y: 210 - barHeight,
          width: 12, height: barHeight, rx: 3, fill: field.color});
        bar.append(node("title", {}, `${point.label} · ${field.label}: ${point[field.key].toLocaleString("pt-BR")}`));
        svg.append(bar);
      });
      if (index % 2 === 0 || index === data.length - 1) {
        svg.append(node("text", {x, y: 235, "font-size": 12, fill: "#425a67"}, point.label));
      }
    });
    target.replaceChildren(svg);
    const legend = document.createElement("p");
    legend.className = "chart-legend";
    for (const field of fields) {
      const label = document.createElement("span");
      label.textContent = field.label;
      const dot = document.createElement("i");
      dot.style.backgroundColor = field.color;
      label.prepend(dot);
      legend.append(label);
    }
    target.append(legend);
  }
  chart("revenue-chart", [
    {key: "received", label: "Recebido (R$)", color: "#006b50"},
    {key: "refunded", label: "Estornos (R$)", color: "#b54a50"},
    {key: "lost", label: "Baixas como perda (R$)", color: "#b17b18"},
  ]);
  const projection = document.getElementById("projection-series");
  if (projection) chart("projection-chart", [
    {key: "expected", label: "A vencer (R$)", color: "#006b50"},
  ], JSON.parse(projection.textContent));
  chart("companies-chart", [{key: "companies", label: "Novas empresas", color: "#155b87"}]);
})();
