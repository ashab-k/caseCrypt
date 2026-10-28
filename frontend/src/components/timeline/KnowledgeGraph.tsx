"use client";

import * as d3 from "d3";
import { useEffect, useRef } from "react";
import type { GraphLink, GraphNode, KnowledgeGraph as KnowledgeGraphData } from "@/types";

const GROUP_COLOR: Record<string, string> = {
  case: "#0d6e5f",
  party: "#1e2a38",
  law: "#b42318",
  document: "#445566",
  event: "#667788",
};

type SimNode = GraphNode & d3.SimulationNodeDatum;
type SimLink = d3.SimulationLinkDatum<SimNode> & { label?: string };

export function KnowledgeGraph({ graph }: { graph: KnowledgeGraphData | null }) {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const wrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!graph || !svgRef.current || !wrapRef.current) return;
    if (graph.nodes.length === 0) return;

    let width = wrapRef.current.clientWidth || 640;
    const height = 360;

    const nodes: SimNode[] = graph.nodes.map((n) => ({ ...n }));
    const links: SimLink[] = graph.links.map((l: GraphLink) => ({
      source: l.source,
      target: l.target,
      label: l.label,
    }));

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.attr("viewBox", `0 0 ${width} ${height}`).attr("width", "100%").attr("height", height);

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimLink>(links)
          .id((d) => d.id)
          .distance(90),
      )
      .force("charge", d3.forceManyBody().strength(-220))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide(28));

    const link = svg
      .append("g")
      .attr("stroke", "#c8d0d8")
      .attr("stroke-opacity", 0.85)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", 1.2);

    const drag = d3
      .drag<SVGGElement, SimNode>()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on("drag", (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    const node = svg
      .append("g")
      .selectAll<SVGGElement, SimNode>("g")
      .data(nodes)
      .join("g")
      .call(drag);

    node.append("title").text((d) => d.label);

    node
      .append("circle")
      .attr("r", (d) => (d.group === "case" ? 14 : 9))
      .attr("fill", (d) => GROUP_COLOR[d.group] || "#667788")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5);

    const labels = node
      .append("text")
      .text((d) => d.label)
      .attr("x", 12)
      .attr("y", 4)
      .attr("font-size", 11)
      .attr("fill", "#1e2a38");

    function updateLabels() {
      const limit = Math.max(12, Math.floor((width / 2 - 35) / 6));
      labels.text((d) => d.label.length > limit ? `${d.label.slice(0, limit - 1)}…` : d.label);
    }
    updateLabels();
    const observer = new ResizeObserver(([entry]) => {
      if (!entry.contentRect.width) return;
      width = entry.contentRect.width;
      svg.attr("viewBox", `0 0 ${width} ${height}`);
      simulation.force("center", d3.forceCenter(width / 2, height / 2)).alpha(0.3).restart();
      updateLabels();
    });
    observer.observe(wrapRef.current);

    simulation.on("tick", () => {
      for (const d of nodes) {
        d.x = Math.max(20, Math.min(width - 20, d.x ?? width / 2));
        d.y = Math.max(20, Math.min(height - 20, d.y ?? height / 2));
      }
      labels.attr("x", (d) => (d.x ?? 0) > width / 2 ? -16 : 16)
        .attr("text-anchor", (d) => (d.x ?? 0) > width / 2 ? "end" : "start");
      link
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);
      node.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => {
      observer.disconnect();
      simulation.stop();
    };
  }, [graph]);

  if (!graph || graph.nodes.length <= 1) {
    return (
      <div className="border border-dashed border-line bg-white/70 p-5">
        <h2 className="text-lg font-semibold text-ink">Knowledge graph</h2>
        <p className="mt-2 text-sm text-muted">
          Entity relations render here once extraction finds parties, provisions,
          or events.
        </p>
      </div>
    );
  }

  return (
    <div className="border border-line bg-white p-5 animate-fade-in">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-ink">Knowledge graph</h2>
        <p className="text-xs text-muted">
          {graph.nodes.length} nodes · {graph.links.length} links · drag to explore
        </p>
      </div>
      <div ref={wrapRef} className="mt-4 overflow-hidden bg-paper-deep/40">
        <svg ref={svgRef} role="img" aria-label="Case knowledge graph" />
      </div>
      <ul className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
        {Object.entries(GROUP_COLOR).map(([group, color]) => (
          <li key={group} className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color }} />
            {group}
          </li>
        ))}
      </ul>
    </div>
  );
}
