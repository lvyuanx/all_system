/**
 * 转 Decimal（自动处理 null/undefined/""）
 */
function toDecimal(v) {
  if (v === null || v === undefined || v === "") {
    return new Decimal(0);
  }
  return new Decimal(v);
}

/**
 * 加法
 */
export function decimalAdd(...values) {
  return values.reduce((sum, v) => sum.plus(toDecimal(v)), new Decimal(0));
}

/**
 * 减法：从第一个开始依次减后面的
 */
export function decimalSub(first, ...values) {
  return values.reduce((res, v) => res.minus(toDecimal(v)), toDecimal(first));
}

/**
 * 乘法
 */
export function decimalMul(...values) {
  if (values.length === 0) return new Decimal(0);
  return values.reduce((res, v) => res.times(toDecimal(v)), new Decimal(1));
}

/**
 * 除法：从第一个开始依次除后面的
 */
export function decimalDiv(first, ...values) {
  return values.reduce((res, v) => res.div(toDecimal(v)), toDecimal(first));
}
