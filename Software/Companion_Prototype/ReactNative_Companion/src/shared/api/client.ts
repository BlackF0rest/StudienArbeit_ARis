import { getConnectionState } from '@shared/state/store';

const DEFAULT_TIMEOUT_MS = 8_000;
const DEFAULT_RETRIES = 2;
const DEFAULT_RETRY_DELAY_MS = 300;

export type BackendEnvelope<T> = {
  ok: boolean;
  data?: T;
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
  timestamp?: string;
  trace_id?: string;
};

export type ApiErrorCode =
  | 'network_error'
  | 'timeout'
  | 'http_error'
  | 'invalid_response'
  | 'unknown_error';

export class ApiClientError extends Error {
  readonly code: ApiErrorCode;
  readonly status?: number;
  readonly details?: unknown;
  readonly traceId?: string;
  readonly backendCode?: string;

  constructor(params: {
    code: ApiErrorCode;
    message: string;
    status?: number;
    details?: unknown;
    traceId?: string;
    backendCode?: string;
  }) {
    super(params.message);
    this.name = 'ApiClientError';
    this.code = params.code;
    this.status = params.status;
    this.details = params.details;
    this.traceId = params.traceId;
    this.backendCode = params.backendCode;
  }
}

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

type RequestOptions = {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  timeoutMs?: number;
  retries?: number;
  traceId?: string;
};

const isReadMethod = (method: HttpMethod) => method === 'GET';

const delay = (durationMs: number) => new Promise(resolve => setTimeout(resolve, durationMs));

const buildUrl = (baseUrl: string, path: string) => {
  const normalizedBase = baseUrl.replace(/\/+$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
};

const mapFetchError = (error: unknown): ApiClientError => {
  if (error instanceof ApiClientError) {
    return error;
  }

  if (error instanceof Error && error.name === 'AbortError') {
    return new ApiClientError({
      code: 'timeout',
      message: 'The request timed out'
    });
  }

  if (error instanceof Error) {
    return new ApiClientError({
      code: 'network_error',
      message: error.message
    });
  }

  return new ApiClientError({
    code: 'unknown_error',
    message: 'Unknown error while performing request',
    details: error
  });
};

const parseEnvelope = <T>(payload: unknown, fallbackTraceId?: string): { data: T; timestamp?: string; traceId?: string } => {
  if (!payload || typeof payload !== 'object') {
    throw new ApiClientError({
      code: 'invalid_response',
      message: 'Response payload is not a JSON object'
    });
  }

  const envelope = payload as BackendEnvelope<T>;
  const traceId = envelope.trace_id ?? fallbackTraceId;

  if (!('ok' in envelope)) {
    throw new ApiClientError({
      code: 'invalid_response',
      message: 'Response does not match expected envelope format',
      traceId
    });
  }

  if (!envelope.ok) {
    throw new ApiClientError({
      code: 'http_error',
      message: envelope.error?.message ?? 'Backend returned an error response',
      details: envelope.error?.details,
      traceId,
      backendCode: envelope.error?.code
    });
  }

  return {
    data: envelope.data as T,
    timestamp: envelope.timestamp,
    traceId
  };
};

export const apiRequest = async <T>(path: string, options: RequestOptions = {}): Promise<T> => {
  const method = options.method ?? 'GET';
  const connection = getConnectionState();
  const requestUrl = buildUrl(connection.baseUrl, path);
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const retries = isReadMethod(method) ? (options.retries ?? DEFAULT_RETRIES) : 0;
  const traceId = options.traceId ?? connection.traceId;

  let attempt = 0;
  let lastError: ApiClientError | undefined;

  while (attempt <= retries) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(requestUrl, {
        method,
        signal: controller.signal,
        headers: {
          Accept: 'application/json',
          ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}),
          ...(traceId ? { 'X-Trace-ID': traceId } : {}),
          ...options.headers
        },
        ...(options.body !== undefined ? { body: JSON.stringify(options.body) } : {})
      });

      let payload: unknown;
      try {
        payload = (await response.json()) as unknown;
      } catch (error) {
        throw new ApiClientError({
          code: 'invalid_response',
          message: 'Response body is not valid JSON',
          status: response.status,
          details: error,
          traceId: response.headers.get('X-Trace-ID') ?? traceId
        });
      }

      if (!response.ok) {
        const envelope = payload as BackendEnvelope<never>;
        throw new ApiClientError({
          code: 'http_error',
          message: envelope?.error?.message ?? `Request failed with HTTP ${response.status}`,
          status: response.status,
          details: envelope?.error?.details,
          traceId: envelope?.trace_id ?? response.headers.get('X-Trace-ID') ?? traceId,
          backendCode: envelope?.error?.code
        });
      }

      const parsed = parseEnvelope<T>(payload, response.headers.get('X-Trace-ID') ?? traceId);
      return parsed.data;
    } catch (error) {
      lastError = mapFetchError(error);
      const shouldRetry = isReadMethod(method) && attempt < retries;
      if (!shouldRetry) {
        throw lastError;
      }

      await delay(DEFAULT_RETRY_DELAY_MS * 2 ** attempt);
      attempt += 1;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  throw (
    lastError ??
    new ApiClientError({
      code: 'unknown_error',
      message: 'Request failed with an unknown error'
    })
  );
};

export const getHealthUrl = (): string => buildUrl(getConnectionState().baseUrl, '/health');
