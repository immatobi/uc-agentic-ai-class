import { IHelper } from "./interfaces.util";

const capitalize = (val: string) => {
    return val.charAt(0).toUpperCase() + val.slice(1).toLowerCase()
}

const capitalizeWord = (value: string): string => {

    let result: string = '';

    if (value.includes('-')) {

        const split = value.split("-");

        for (var i = 0; i < split.length; i++) {
            split[i] = split[i].charAt(0).toUpperCase() + split[i].slice(1);
        }

        result = split.join('-')

    } else {
        const split = value.split(" ");

        for (var i = 0; i < split.length; i++) {
            split[i] = split[i].charAt(0).toUpperCase() + split[i].slice(1);
        }

        result = split.join(' ')
    }

    return result;

}

const humanizeLabel = (value: string): string => {
    return capitalizeWord(value.replace(/_/g, " "));
}

const helper: IHelper = {
    capitalize: capitalize,
    capitalizeWord: capitalizeWord,
    humanizeLabel: humanizeLabel
}

export default helper;