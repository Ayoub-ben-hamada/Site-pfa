declare module 'react-plotly.js' {
  import * as Plotly from 'plotly.js'
  import * as React from 'react'

  interface PlotParams {
    data: Plotly.Data[]
    layout?: Partial<Plotly.Layout>
    config?: Partial<Plotly.Config>
    frames?: Plotly.Frame[]
    onInitialized?: (figure: Readonly<Figure>, graphDiv: Readonly<HTMLElement>) => void
    onUpdate?: (figure: Readonly<Figure>, graphDiv: Readonly<HTMLElement>) => void
    onPurge?: (figure: Readonly<Figure>, graphDiv: Readonly<HTMLElement>) => void
    onError?: (err: Readonly<Error>) => void
    onBeforePlot?: (event: Readonly<Plotly.BeforePlotEvent>) => boolean
    onClick?: (event: Readonly<Plotly.PlotMouseEvent>) => void
    onClickAnnotation?: (event: Readonly<Plotly.ClickAnnotationEvent>) => void
    onHover?: (event: Readonly<Plotly.PlotHoverEvent>) => void
    onUnhover?: (event: Readonly<Plotly.PlotMouseEvent>) => void
    onSelected?: (event: Readonly<Plotly.PlotSelectionEvent>) => void
    onRelayout?: (event: Readonly<Plotly.PlotRelayoutEvent>) => void
    onRestyle?: (event: Readonly<Plotly.PlotRestyleEvent>) => void
    onRedraw?: () => void
    onAutoSize?: () => void
    onAnimated?: () => void
    onAfterExport?: () => void
    onAfterPlot?: () => void
    onAnimatingFrame?: (event: Readonly<Plotly.FrameAnimationEvent>) => void
    onAnimationInterrupted?: () => void
    onFramework?: () => void
    onTransitioning?: () => void
    onTransitionInterrupted?: () => void
    onDeselect?: () => void
    onDoubleClick?: () => void
    onLegendClick?: (event: Readonly<Plotly.LegendClickEvent>) => boolean
    onLegendDoubleClick?: (event: Readonly<Plotly.LegendClickEvent>) => boolean
    onSliderChange?: (event: Readonly<Plotly.SliderChangeEvent>) => void
    onSliderEnd?: (event: Readonly<Plotly.SliderEndEvent>) => void
    onSliderStart?: (event: Readonly<Plotly.SliderStartEvent>) => void
    onSunburstClick?: (event: Readonly<Plotly.SunburstClickEvent>) => void
    onButtonClicked?: (event: Readonly<Plotly.ButtonClickEvent>) => void
    divId?: string
    className?: string
    style?: React.CSSProperties
    debug?: boolean
    useResizeHandler?: boolean
    revision?: number
  }

  interface Figure {
    data: Plotly.Data[]
    layout: Partial<Plotly.Layout>
    frames?: Plotly.Frame[]
  }

  const Plot: React.ComponentType<PlotParams>
  export default Plot
}
