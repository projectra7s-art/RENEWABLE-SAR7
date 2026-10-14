// Number / unit formatting used by the results panel.

export function num(value, decimals = 1) {
  return Number(value).toLocaleString("en-US", {
    maximumFractionDigits: decimals,
  });
}

// data-fmt="..." name -> formatter
export const FORMATTERS = {
  text: (v) => String(v),
  int:  (v) => num(v, 0),
  kw:   (v) => `${num(v, 2)} kW`,
  kwh:  (v) => `${num(v, 1)} kWh`,
  w:    (v) => `${num(v, 0)} W`,
  sar:  (v) => `${num(v, 0)} SAR`,
  pct:  (v) => `${num(v, 1)}%`,
  mps:  (v) => `${num(v, 2)} m/s`,
  wm2:  (v) => `${num(v, 1)} W/m²`,
  m:    (v) => `${num(v, 0)} m`,
  c:    (v) => `${num(v, 1)} °C`,
  rho:  (v) => `${num(v, 3)} kg/m³`,
  num3: (v) => num(v, 3),
  sarkwh: (v) => `${num(v, 3)} SAR/kWh`,
};
