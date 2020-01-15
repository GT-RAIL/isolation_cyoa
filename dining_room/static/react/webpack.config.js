const path = require('path');
const webpack = require('webpack');

module.exports = {
    entry: "./src/index.js",
    mode: "development",
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /(node_modules|bower_components)/,
                loader: "babel-loader",
                options: { presets: ["@babel/env"] }
            },
            {
                test: /\.css$/,
                use: ["style-loader", "css-loader"]
            }
        ]
    },
    resolve: { extensions: ["*", ".js", ".jsx"] },
    output: {
        path: path.resolve(__dirname, "../dining_room/"),
        publicPath: "/static/dining_room/",
        filename: "study.js"
    },
    devServer: {
        contentBase: __dirname,
        port: 9000,
        publicPath: "http://localhost:9000/static/dining_room/",
        hotOnly: true
    },
    plugins: [new webpack.HotModuleReplacementPlugin()]
};
