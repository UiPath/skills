// The data-fetch signature every metric module exports.
//
// sdk is `any` because the SDK service constructors take `sdk as never`; the
// array return preserves the settled Promise<any[]> harness — SDK response
// interfaces lack implicit index signatures and are not assignable to
// Record<string, unknown>[], so any[] accepts SDK-typed arrays directly while
// still requiring an array return.
export type MetricFn = (sdk: any, getToken: () => Promise<string>) => Promise<any[]>

// The keyed-detail signature for row-click drill-downs. A table widget with a
// `rowLink` exports this so "click THIS row → fetch THAT entity's records"
// (e.g. fetchDetailByKey(sdk, agentName) → that agent's most recent trace spans).
// `key` is the clicked row's link field value (route param).
export type MetricDetailByKeyFn = (sdk: any, key: string, getToken: () => Promise<string>) => Promise<any[]>
