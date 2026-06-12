import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'humanReadableAmount',
  standalone: true
})
export class HumanReadableAmountPipe implements PipeTransform {
  transform(value: number | string | null | undefined): string {
    if (value == null) return '0';
    let val = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(val)) return '0';

    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)}Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)}L`;
    return `₹${val.toLocaleString()}`;
  }
}
