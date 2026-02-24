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


/**
 * 比较两个数大小
 * 返回：
 *  1  => a > b
 *  0  => a === b
 * -1  => a < b
 */
export function decimalCompare(a, b) {
  return toDecimal(a).comparedTo(toDecimal(b));
}

/**
 * 是否大于
 */
export function decimalGt(a, b) {
  return toDecimal(a).gt(toDecimal(b));
}

/**
 * 是否大于等于
 */
export function decimalGte(a, b) {
  return toDecimal(a).gte(toDecimal(b));
}

/**
 * 是否小于
 */
export function decimalLt(a, b) {
  return toDecimal(a).lt(toDecimal(b));
}

/**
 * 是否小于等于
 */
export function decimalLte(a, b) {
  return toDecimal(a).lte(toDecimal(b));
}

/**
 * 是否相等
 */
export function decimalEq(a, b) {
  return toDecimal(a).eq(toDecimal(b));
}