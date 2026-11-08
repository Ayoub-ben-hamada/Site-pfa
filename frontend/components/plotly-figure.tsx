"use client"

import dynamic from "next/dynamic"

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false })

interface PlotlyFigureProps {
  figure?: {
    data?: any[]
    layout?: Record<string, unknown>
    frames?: any[]
  }
  height?: number
}

export function PlotlyFigure({ figure, height = 320 }: PlotlyFigureProps) {
  if (!figure?.data?.length) {
    return null
  }

  return (
    <Plot
      data={figure.data}
      layout={{
        autosize: true,
        margin: { l: 40, r: 16, t: 48, b: 36 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        ...(figure.layout || {}),
      }}
      config={{ responsive: true, displaylogo: false }}
      style={{ width: "100%", height }}
      useResizeHandler
      frames={figure.frames}
    />
  )
}
