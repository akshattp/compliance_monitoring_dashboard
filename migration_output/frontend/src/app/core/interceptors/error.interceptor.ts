import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An unknown error occurred';
      
      if (error.error instanceof ErrorEvent) {
        // Client-side or network error
        errorMessage = `Client Error: ${error.error.message}`;
      } else {
        // Backend returned an unsuccessful response code
        errorMessage = `Backend Error - Status: ${error.status}\nMessage: ${error.message}\nBody: ${JSON.stringify(error.error)}`;
      }

      console.group('%c API Error', 'color: white; background-color: red; padding: 2px 4px; border-radius: 2px');
      console.log(`URL: ${req.url}`);
      console.log(`Method: ${req.method}`);
      if (req.body && typeof req.body === 'object' && !(req.body instanceof FormData)) {
        // Truncate payload if it's too large (e.g. dataframes)
        const payloadStr = JSON.stringify(req.body);
        if (payloadStr.length > 500) {
            console.log(`Payload (truncated):`, req.body);
        } else {
            console.log(`Payload:`, req.body);
        }
      }
      console.error(errorMessage);
      console.groupEnd();

      // Optionally show a user-friendly error toast here if a global toaster service exists

      return throwError(() => error);
    })
  );
};
