import { ApiMethodType } from "../utils/types.util";

export interface CallAPIDTO {
    type: 'backend' | 'service',
    method: ApiMethodType,
    path: string,
    isAuth?: boolean,
    payload?: any
}