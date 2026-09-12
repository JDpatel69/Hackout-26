export const email=(value:string)=>/^\S+@\S+\.\S+$/.test(value)?'':'Enter a valid email address.';
export const required=(value:string,label='This field')=>value.trim()?'':`${label} is required.`;
export const password=(value:string)=>value.length>=4?'':'Use at least 4 characters.';
