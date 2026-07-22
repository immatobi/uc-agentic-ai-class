
import Axios from 'axios'
import { IAPIResponse } from "../utils/interfaces.util";
import { CallAPIDTO } from '@/dtos/axios.dto';

class AxiosService {

    public baseUrl: string;
    constructor() {

        if (!process.env.NEXT_PUBLIC_API_URL) {
            throw new Error('API base url not defined')
        }
        
        this.baseUrl = process.env.NEXT_PUBLIC_API_URL;

    }

    /**
     * @name call
     * @param params 
     * @returns 
     */
    public async call(params: CallAPIDTO): Promise<IAPIResponse> {

        let result: any = {}
        const { method, path, payload } = params;

        let urlpath = `${this.baseUrl}${path}`;

        await Axios({
            method: method,
            url: urlpath,
            data: payload,
            headers: {}
        }).then((resp) => {
            result = resp.data;
        }).catch((err) => {

            if (err.response && err.response.data) {

                const { data, errors, status } = err.response.data

                result.error = true;
                result.errors = errors;
                result.message = 'An error occured'
                result.data = data || null
                result.status = status

            } else if (typeof (err) === 'object') {
                result.error = true;
                result.errors = ['an error occurred. please try again']
                result.message = 'Error';
                result.data = err;
            } else if (typeof (err) === 'string') {
                result.error = true;
                result.errors = [err.toString()]
                result.message = err.toString();
                result.data = err.toString()
            }

        })

        return result;

    }

}

export default new AxiosService()