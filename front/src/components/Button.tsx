import React from "react";
import styles from './Button.module.css';
import classNames from "classnames/bind";

const cx = classNames.bind(styles);

const Button: React.FC<any> = ({ children, wide, gold, blue, type = "button", onClick = () => {} }) => (
    <button type={type} className={cx('Button', {
        Wide: wide,
        Gold: gold,
        Blue: blue
    })}
        onClick={onClick}
    >
        {children}
    </button>
);

export { Button };

