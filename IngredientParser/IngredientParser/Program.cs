using FluentNHibernate.Cfg.Db;
using KitchenPC;
using KitchenPC.Context;
using KitchenPC.DB;
using KitchenPC.DB.Search;
using KitchenPC.NLP;
using KitchenPC.Recipes;
using System;
using System.Diagnostics;
using System.IO;

namespace IngredientParser
{
    class Program
    {
        static void Main(string[] args)
        {
            string dataPath = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..\\..\\..\\data"));
            // Context connected to local data store
            var staticConfig = Configuration<StaticContext>.Build
               .Context(StaticContext.Configure
                  .DataDirectory(dataPath)
                  .Identity(() => new AuthIdentity(new Guid("c52a2874-bf95-4b50-9d45-a85a84309e75"), "Mike"))
               )
               .Create();
            KPCContext.Initialize(staticConfig);

            var context = KPCContext.Current;

            var result = context.ParseIngredient("1 teaspoon of salt");
            Console.WriteLine("here");
            result = context.ParseIngredient("2 pounds chicken wings ");
            Console.WriteLine(result.Name);
            result = context.ParseIngredient("1(18.25 ounce) package marble cake mix");
            Console.WriteLine(result.Name);
            result = context.ParseIngredient("2 cups milk");
            Console.WriteLine(result.Name);
            result = context.ParseIngredient(" 1 teaspoon vanilla extract");
            Console.WriteLine(result.Name);

            // The following will not be correctly parsed!

            //result = context.ParseIngredient("2 teaspoons dry ranch dressing mix");
            //Console.WriteLine(result.Name);
            //result = context.ParseIngredient("1(3.5 ounce) package sliced pepperoni");
            //Console.WriteLine(result.Name);
            //result = context.ParseIngredient(" 1 (12 inch) pre-baked pizza crust");
            //Console.WriteLine(result.Name);
            //result = context.ParseIngredient("1 (12 ounce) package Johnsonville® Three Cheese Italian Style Chicken Sausage, sliced");
            //Console.WriteLine(result.Name);
        }
    }
}
