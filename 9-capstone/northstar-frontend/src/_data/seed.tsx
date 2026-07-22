import { BarChart3Icon, FileTextIcon, LineChartIcon, MailPlusIcon } from 'lucide-react'

const UIPrompts = [
    {
        icon: <MailPlusIcon strokeWidth={1.8} className="size-5 pag-800"/>,
        text: 'How do I connect my email account?'
    },
    {
        icon: <LineChartIcon strokeWidth={1.8} className="size-5 pag-800"/>,
        text: 'Create an onboarding checklist for my team.'
    },
    {
        icon: <FileTextIcon strokeWidth={1.8} className="size-5 pag-800"/>,
        text: 'I was charged twice this month. Why?'
    },
    {
        icon: <BarChart3Icon strokeWidth={1.8} className="size-5 pag-800"/>,
        text: 'What is included in the Pro plan?'
    }
]

export {
    UIPrompts,
};