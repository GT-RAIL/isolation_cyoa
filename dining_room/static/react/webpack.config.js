const path = require('path');
const webpack = require('webpack');
const TerserJSPlugin = require('terser-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');

module.exports = {
    entry: {
        index: "./src/index.js",
    },
    mode: "development",
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/i,
                exclude: /(node_modules|bower_components)/,
                loader: "babel-loader",
                options: { presets: ["@babel/env"] }
            },
            {
                test: /\.(js|jsx)$/i,
                use: 'react-hot-loader/webpack',
                include: /node_modules/
            },
            {
                test: /\.(sa|sc|c)ss$/i,
                use: [
                    {
                        loader: MiniCssExtractPlugin.loader,
                        options: {
                            publicPath: '/static/dining_room/',
                            hmr: process.env.NODE_ENV === 'development'
                        }
                    },
                    "css-loader",
                    {
                        loader: "postcss-loader",
                        options: {
                            plugins: function() {
                                return [
                                    require('precss'),
                                    require('autoprefixer')
                                ];
                            }
                        }
                    },
                    "sass-loader"
                ]
            }
        ]
    },
    resolve: {
        extensions: ["*", ".js", ".jsx"]
    },
    output: {
        path: path.resolve(__dirname, "../dining_room/"),
        publicPath: "/static/dining_room/",
        filename: "[name].js"
    },
    optimization: {
        minimizer: [new TerserJSPlugin({}), new OptimizeCSSAssetsPlugin({})]
    },
    devServer: {
        contentBase: __dirname,
        port: 9000,
        publicPath: "http://localhost:9000/static/dining_room/",
        hotOnly: true
    },
    plugins: [
        new webpack.HotModuleReplacementPlugin(),
        new MiniCssExtractPlugin({ filename: "[name].css", chunkFilename: '[id].css' })
    ]
};
