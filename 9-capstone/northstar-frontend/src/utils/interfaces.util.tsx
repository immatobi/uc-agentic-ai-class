export interface IAPIResponse {
    error: boolean,
    errors: Array<any>
    data: IChatResponseData,
    message: string,
    status: number
}

export interface IChatResponseData {
    question: string,
    customer_id: string;
    thread_id: string;
    route: string,
    answer: any,
    review: any,
    confidence: number | string,
    priority: string,
    assigned_team: string,
    sources: Array<any>,
    memory_updates: Array<any>,
}

export interface IHelper{
    capitalize(val: string): string;
    capitalizeWord(value: string): string;
    humanizeLabel(value: string): string;
}