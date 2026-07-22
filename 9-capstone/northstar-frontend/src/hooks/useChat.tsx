import axiosService from "@/services/axios.service"
import { useCallback, useEffect, useState } from "react"

interface IChat{
    question: string,
    thread_id?: string,
    customer_id?: string
}

const useChat = () => {

    useEffect(() => {

    }, [])

    const [loading, setLoading] = useState<boolean>(false)

    const chat = useCallback(async(data: IChat) => {

        setLoading(true)

        const response = await axiosService.call({
            method: 'POST',
            type: 'backend',
            isAuth: false,
            path: '/v1/chat',
            payload: {
                question: data.question,
                thread_id: data.thread_id || '',
                customer_id: data.customer_id || ''
            }
        })

        setLoading(false)

        return response

    }, [setLoading])

    return {
        loading,
        chat
    }

}

export default useChat